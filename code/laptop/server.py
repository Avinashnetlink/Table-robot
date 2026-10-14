"""Bob laptop server.

Bob connects to ws://<laptop-ip>:8765/bob. This server:
  - prints Bob's status and events,
  - hears "Hey Bob" in the microphone stream (needs faster-whisper),
  - answers simple commands and speaks through Bob's speaker,
  - saves photos and, if pytesseract is installed, reads the text in them,
  - keeps reminders in SQLite and speaks them when they are due.

Type `help` in this window for console commands.
"""

from __future__ import annotations

import argparse
import array
import asyncio
import datetime as dt
import json
import math
import os
import pathlib
import re
import sqlite3
import sys
import tempfile
import threading
import time
import wave

from websockets.asyncio.server import serve

try:
    import numpy as np
    from faster_whisper import WhisperModel
except ImportError:
    np = None
    WhisperModel = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

HERE = pathlib.Path(__file__).resolve().parent
PHOTOS = HERE / "photos"
DB_PATH = HERE / "reminders.db"

RATE = 16000
TAG_MIC, TAG_IMAGE, TAG_PLAY = ord("A"), ord("I"), ord("P")
PLAY_CHUNK_SAMPLES = 2048  # 128 ms; keeps each frame well under Bob's receive limit
LISTEN_TIMEOUT_S = 10
WAKE_PHRASE = "hey bob"


def log(*parts: object) -> None:
    print(time.strftime("%H:%M:%S"), *parts, flush=True)


def normalize(text: str) -> str:
    return " ".join("".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text).split())


# ---------------------------------------------------------------- speech out
async def synthesize(text: str) -> bytes:
    """Text to 16 kHz 16-bit mono PCM. Windows built-in voice, or pyttsx3 elsewhere."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "say.wav")
        env = dict(os.environ, BOB_TEXT=text, BOB_WAV=path)
        if sys.platform == "win32":
            script = (
                "Add-Type -AssemblyName System.Speech;"
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                "$f = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo("
                "16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,"
                " [System.Speech.AudioFormat.AudioChannel]::Mono);"
                "$s.SetOutputToWaveFile($env:BOB_WAV, $f); $s.Speak($env:BOB_TEXT); $s.Dispose()"
            )
            cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]
        else:
            code = (
                "import os, pyttsx3; e = pyttsx3.init();"
                "e.save_to_file(os.environ['BOB_TEXT'], os.environ['BOB_WAV']); e.runAndWait()"
            )
            cmd = [sys.executable, "-c", code]
        proc = await asyncio.create_subprocess_exec(*cmd, env=env)
        await proc.wait()
        if not os.path.exists(path):
            raise RuntimeError("text-to-speech produced no audio")
        return wav_to_pcm16k(path)


def wav_to_pcm16k(path: str) -> bytes:
    with wave.open(path, "rb") as w:
        rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        frames = w.readframes(w.getnframes())
    if width != 2:
        raise RuntimeError(f"expected 16-bit audio, got {8 * width}-bit")
    samples = array.array("h", frames)
    if sys.byteorder == "big":
        samples.byteswap()
    if channels > 1:
        samples = array.array("h", samples[::channels])
    if rate != RATE:
        ratio = rate / RATE
        n = int(len(samples) / ratio)
        out = array.array("h", bytes(2 * n))
        for i in range(n):
            pos = i * ratio
            j = int(pos)
            k = min(j + 1, len(samples) - 1)
            out[i] = int(samples[j] + (samples[k] - samples[j]) * (pos - j))
        samples = out
    return samples.tobytes()


def scale_pcm(pcm: bytes, volume: float) -> bytes:
    s = array.array("h", pcm)
    for i, v in enumerate(s):
        s[i] = max(-32768, min(32767, int(v * volume)))
    return s.tobytes()


# ---------------------------------------------------------------- speech in
class Segmenter:
    """Cuts the microphone stream into utterances with a simple energy detector."""

    def __init__(self) -> None:
        self.noise = 200.0
        self.active = False
        self.buf = bytearray()
        self.pre = bytearray()
        self.silent_ms = 0

    def feed(self, pcm: bytes) -> bytes | None:
        s = array.array("h", pcm)
        if not s:
            return None
        mean = sum(s) / len(s)
        rms = math.sqrt(sum((v - mean) ** 2 for v in s) / len(s))
        ms = 1000 * len(s) / RATE
        loud = rms > max(3 * self.noise, 300)
        if not loud:
            self.noise = 0.95 * self.noise + 0.05 * rms

        if not self.active:
            self.pre += pcm
            del self.pre[: max(0, len(self.pre) - RATE * 2 // 4)]  # keep 250 ms before speech
            if loud:
                self.active, self.silent_ms = True, 0
                self.buf = bytearray(self.pre)
            return None

        self.buf += pcm
        self.silent_ms = 0 if loud else self.silent_ms + ms
        if self.silent_ms > 700 or len(self.buf) > RATE * 2 * 8:
            self.active = False
            out, self.buf = bytes(self.buf), bytearray()
            return out if len(out) > RATE * 2 * 0.3 else None
        return None

    @property
    def speaking(self) -> bool:
        return self.active


class Transcriber:
    def __init__(self, model_name: str) -> None:
        self.model = None
        if WhisperModel is None:
            log("Speech-to-text off: pip install faster-whisper numpy  (console `hey ...` still works)")
            return
        log(f"Loading faster-whisper model '{model_name}' ...")
        self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
        log("Speech-to-text ready.")

    def transcribe(self, pcm: bytes) -> str:
        if self.model is None:
            return ""
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(audio, language="en", beam_size=1)
        return " ".join(seg.text.strip() for seg in segments).strip()


# ---------------------------------------------------------------- reminders
class Reminders:
    def __init__(self, path: pathlib.Path) -> None:
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS reminders ("
            " id INTEGER PRIMARY KEY, due TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'task',"
            " title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
        )
        self.db.commit()

    def add(self, due: dt.datetime, title: str, kind: str = "task") -> int:
        cur = self.db.execute(
            "INSERT INTO reminders (due, kind, title) VALUES (?, ?, ?)", (due.isoformat(timespec="minutes"), kind, title)
        )
        self.db.commit()
        return cur.lastrowid

    def due(self) -> list[tuple[int, str, str]]:
        now = dt.datetime.now().isoformat(timespec="minutes")
        return self.db.execute(
            "SELECT id, kind, title FROM reminders WHERE done = 0 AND due <= ? ORDER BY due", (now,)
        ).fetchall()

    def pending(self) -> list[tuple[int, str, str, str]]:
        return self.db.execute("SELECT id, due, kind, title FROM reminders WHERE done = 0 ORDER BY due").fetchall()

    def done(self, rid: int) -> None:
        self.db.execute("UPDATE reminders SET done = 1 WHERE id = ?", (rid,))
        self.db.commit()


def parse_when(words: list[str]) -> tuple[dt.datetime, list[str]] | None:
    """'18:30 ...' (today or tomorrow) or '2026-10-14 18:30 ...'."""
    now = dt.datetime.now()
    try:
        if len(words) >= 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", words[0]):
            when = dt.datetime.fromisoformat(f"{words[0]} {words[1]}")
            return when, words[2:]
        if words and re.fullmatch(r"\d{1,2}:\d{2}", words[0]):
            h, m = map(int, words[0].split(":"))
            when = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if when <= now:
                when += dt.timedelta(days=1)
            return when, words[1:]
    except ValueError:
        return None
    return None


# ---------------------------------------------------------------- Bob link
class Bob:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.ws = None
        self.status: dict = {}
        self.listening_until = 0.0
        self.segmenter = Segmenter()
        self.transcriber = Transcriber(args.model) if not args.no_stt else None
        self.reminders = Reminders(DB_PATH)
        self.photo_waiter: asyncio.Future | None = None
        self.last_keep_awake = 0.0
        self.say_lock = asyncio.Lock()
        self.tasks: set[asyncio.Task] = set()

    # -- sending
    async def send(self, **msg: object) -> None:
        if self.ws is not None:
            await self.ws.send(json.dumps(msg))

    async def say(self, text: str) -> None:
        log(f"Bob says: {text}")
        await self.send(type="show", line1=text[:21], line2=text[21:42], ms=max(3000, 80 * len(text)))
        if self.ws is None:
            return
        try:
            pcm = scale_pcm(await synthesize(text), self.args.volume)
        except Exception as exc:  # noqa: BLE001 - speech is optional, the OLED already shows the text
            log(f"(no voice: {exc})")
            return
        async with self.say_lock:
            await self.send(type="say_start")
            step = PLAY_CHUNK_SAMPLES * 2
            start = time.monotonic()
            for i in range(0, len(pcm), step):
                if self.ws is None:
                    return
                await self.ws.send(bytes([TAG_PLAY]) + pcm[i : i + step])
                ahead = (i + step) / 2 / RATE - (time.monotonic() - start)
                if ahead > 0.3:  # stay at most 300 ms ahead of playback
                    await asyncio.sleep(ahead - 0.3)
            await self.send(type="say_end")

    async def take_photo(self, timeout: float = 5.0) -> pathlib.Path | None:
        loop = asyncio.get_running_loop()
        self.photo_waiter = loop.create_future()
        await self.send(type="photo")
        try:
            return await asyncio.wait_for(self.photo_waiter, timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            self.photo_waiter = None

    # -- receiving
    async def on_text(self, msg: dict) -> None:
        t = msg.get("type")
        if t == "hello":
            log(f"Bob connected, firmware {msg.get('fw')}")
            await self.send(type="show", line1="Hello!", line2="laptop connected", ms=3000)
        elif t == "status":
            changed = {k: msg.get(k) for k in ("unlocked", "patrol", "sensors_ok", "battery_low", "fault")}
            old = {k: self.status.get(k) for k in changed}
            self.status = msg
            if changed != old or self.args.verbose:
                log(
                    f"status: battery {msg.get('battery_v')} V, table {msg.get('table')}, "
                    f"sensors {'ok' if msg.get('sensors_ok') else 'PROBLEM'}, "
                    f"{'unlocked' if msg.get('unlocked') else 'locked'}, patrol {msg.get('patrol')}"
                )
        elif t == "wiring":
            problems = msg.get("problems", 0)
            log(f"wiring check: {'all connections OK' if not problems else f'{problems} problem(s)'}")
            for item in msg.get("items", []):
                if item.get("result") != "OK" or self.args.verbose:
                    log(f"  {item.get('result'):<5} {item.get('part')}: {item.get('detail')}")
        elif t == "event":
            log(f"event: {msg.get('what')} - {msg.get('detail')}")
        elif t != "pong":
            log(f"from Bob: {msg}")

    async def on_binary(self, data: bytes) -> None:
        if not data:
            return
        tag, body = data[0], data[1:]
        if tag == TAG_IMAGE:
            PHOTOS.mkdir(exist_ok=True)
            path = PHOTOS / time.strftime("%Y%m%d-%H%M%S.jpg")
            path.write_bytes(body)
            log(f"photo saved: {path} ({len(body)} bytes)")
            if self.photo_waiter and not self.photo_waiter.done():
                self.photo_waiter.set_result(path)
        elif tag == TAG_MIC:
            utterance = self.segmenter.feed(body)
            now = time.monotonic()
            if self.segmenter.speaking and now - self.last_keep_awake > 5:
                self.last_keep_awake = now
                await self.send(type="keep_awake")
            if utterance and self.transcriber and self.transcriber.model:
                # Never block the receive loop: Bob keeps streaming while this runs.
                self.spawn(self.transcribe_and_handle(utterance))

    def spawn(self, coro) -> None:
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def transcribe_and_handle(self, utterance: bytes) -> None:
        text = await asyncio.get_running_loop().run_in_executor(None, self.transcriber.transcribe, utterance)
        if text:
            await self.heard(text)

    # -- conversation
    async def heard(self, text: str) -> None:
        words = normalize(text)
        log(f"heard: {text!r}")
        now = time.monotonic()
        if now < self.listening_until:
            self.listening_until = 0
            await self.send(type="listen", active=False)
            await self.command(words)
        elif words.startswith(WAKE_PHRASE):
            rest = words[len(WAKE_PHRASE) :].strip()
            if rest:
                await self.command(rest)
            else:
                self.listening_until = now + LISTEN_TIMEOUT_S
                await self.send(type="listen", active=True)
                await self.send(type="show", line1="Listening", line2="", ms=LISTEN_TIMEOUT_S * 1000)

    async def command(self, words: str) -> None:
        await self.send(type="state", state="thinking")
        try:
            await self._command(words)
        finally:
            await self.send(type="state", state="awake")

    async def _command(self, w: str) -> None:
        has = lambda *keys: any(k in w for k in keys)  # noqa: E731
        if has("stop patrol", "stop looking"):
            await self.send(type="patrol", on=False)
            await self.say("Patrol off.")
        elif has("stop", "halt", "freeze"):
            await self.send(type="stop")
            await self.say("Stopped.")
        elif has("patrol", "look around", "explore"):
            await self.send(type="patrol", on=True)
            await self.say("Starting a slow patrol.")
        elif has("turn left"):
            await self.send(type="move", dir="pivot_left", duty=self.args.duty, ms=200)
        elif has("turn right"):
            await self.send(type="move", dir="pivot_right", duty=self.args.duty, ms=200)
        elif has("forward", "come here", "move ahead"):
            await self.send(type="move", dir="forward", duty=self.args.duty, ms=300)
        elif has("time"):
            await self.say(time.strftime("It is %I:%M %p.").replace(" 0", " "))
        elif has("date", "what day", "today"):
            await self.say(dt.date.today().strftime("Today is %A, %B %d."))
        elif has("read", "photo", "picture", "what is this", "look at"):
            await self.read_photo()
        elif has("remind me", "reminder"):
            await self.voice_reminder(w)
        elif has("go to sleep", "sleep now", "good night"):
            await self.say("Good night.")
            await asyncio.sleep(2)
            await self.send(type="sleep")
        else:
            await self.say(f"I heard: {w}")

    async def read_photo(self) -> None:
        await self.send(type="show", line1="Looking...", line2="", ms=3000)
        path = await self.take_photo()
        if path is None:
            await self.say("I could not take a photo.")
            return
        if pytesseract is None:
            await self.say("Photo saved on the laptop.")
            return
        try:
            text = " ".join(pytesseract.image_to_string(Image.open(path)).split())
        except Exception as exc:  # noqa: BLE001 - Tesseract may be missing on PATH
            log(f"OCR failed: {exc}")
            text = ""
        await self.say(f"It says: {text[:200]}" if len(text) >= 3 else "I could not read that.")

    async def voice_reminder(self, w: str) -> None:
        m = re.search(r"remind me (?:to )?(.+?) at (\d{1,2})(?: (\d{2}))? ?(am|pm)?$", w)
        if not m:
            await self.say("Say: remind me to call mom at 6 30 pm.")
            return
        title, h, mi, ap = m.group(1), int(m.group(2)), int(m.group(3) or 0), m.group(4)
        if ap == "pm" and h < 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        when = parse_when([f"{h}:{mi:02d}"])
        if when is None:
            await self.say("I did not understand the time.")
            return
        self.reminders.add(when[0], title)
        await self.say(f"OK. {title} at {when[0].strftime('%I:%M %p').lstrip('0')}.")

    async def reminder_loop(self) -> None:
        while True:
            await asyncio.sleep(10)
            if self.ws is None:
                continue
            for rid, kind, title in self.reminders.due()[:1]:  # one item at a time
                self.reminders.done(rid)
                await self.say(f"Reminder: {title}" if kind == "task" else f"{kind.capitalize()}: {title}")

    # -- console
    async def console(self, line: str) -> None:
        parts = line.strip().split()
        if not parts:
            return
        cmd, args = parts[0].lower(), parts[1:]
        rest = line.strip()[len(parts[0]) :].strip()
        if cmd == "help":
            print(CONSOLE_HELP)
        elif cmd == "say":
            await self.say(rest)
        elif cmd == "show":
            l1, _, l2 = rest.partition("|")
            await self.send(type="show", line1=l1.strip(), line2=l2.strip())
        elif cmd == "photo":
            path = await self.take_photo()
            log(f"photo: {path or 'none arrived'}")
        elif cmd == "read":
            await self.read_photo()
        elif cmd == "patrol":
            await self.send(type="patrol", on=bool(args) and args[0].lower() == "on")
        elif cmd == "move" and args:
            duty = int(args[1]) if len(args) > 1 else self.args.duty
            ms = int(args[2]) if len(args) > 2 else 300
            await self.send(type="move", dir=args[0], duty=duty, ms=ms)
        elif cmd == "stop":
            await self.send(type="stop")
        elif cmd == "sleep":
            await self.send(type="sleep")
        elif cmd == "status":
            print(json.dumps(self.status, indent=2))
        elif cmd == "hey":
            await self.heard(f"{WAKE_PHRASE} {rest}")
        elif cmd == "remind":
            parsed = parse_when(args)
            if not parsed or not parsed[1]:
                print("usage: remind 18:30 text   or   remind 2026-10-14 10:00 [interview|event|learning] text")
                return
            when, words = parsed
            kind = "task"
            if len(words) > 1 and words[0] in ("task", "event", "interview", "learning"):
                kind, words = words[0], words[1:]
            title = " ".join(words)
            rid = self.reminders.add(when, title, kind)
            print(f"#{rid} {kind} at {when:%Y-%m-%d %H:%M}: {title}")
        elif cmd == "list":
            for rid, due, kind, title in self.reminders.pending():
                print(f"#{rid}  {due}  {kind:<9} {title}")
        elif cmd == "done" and args:
            self.reminders.done(int(args[0]))
        else:
            print("unknown command - type help")


CONSOLE_HELP = """
  say <text>                 speak through Bob
  show <line1>|<line2>       text on the OLED
  photo                      take a photo, save it in photos/
  read                       photo + read the text (needs pytesseract)
  patrol on|off              autonomous patrol (Bob must be unlocked by a 2 s touch)
  move <dir> [duty] [ms]     dir: forward, pivot_left, pivot_right
  stop                       stop motors and patrol
  sleep                      deep sleep now
  status                     last status from Bob
  hey <words>                pretend Bob heard "hey bob <words>" (test without speech-to-text)
  remind 18:30 <text>        add a reminder (also: remind 2026-10-14 10:00 interview <text>)
  list | done <id>           reminders
  quit
"""


async def main() -> None:
    p = argparse.ArgumentParser(description="Bob laptop server")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--model", default="base.en", help="faster-whisper model (tiny.en is faster)")
    p.add_argument("--no-stt", action="store_true", help="do not load speech-to-text")
    p.add_argument("--volume", type=float, default=0.6, help="speech volume 0.1-1.0")
    p.add_argument("--duty", type=int, default=30, help="motor duty for voice moves, percent")
    p.add_argument("--verbose", action="store_true", help="print every status message")
    args = p.parse_args()

    bob = Bob(args)

    async def handler(ws) -> None:
        if ws.request.path != "/bob":
            await ws.close(code=1008, reason="use /bob")
            return
        bob.ws = ws
        try:
            async for message in ws:
                if isinstance(message, bytes):
                    await bob.on_binary(message)
                else:
                    await bob.on_text(json.loads(message))
        except Exception as exc:  # noqa: BLE001 - keep the server up whatever one client does
            log(f"connection error: {exc}")
        finally:
            if bob.ws is ws:
                bob.ws = None
                log("Bob disconnected")

    loop = asyncio.get_running_loop()
    lines: asyncio.Queue[str] = asyncio.Queue()

    def read_stdin() -> None:
        for line in sys.stdin:
            loop.call_soon_threadsafe(lines.put_nowait, line)
        loop.call_soon_threadsafe(lines.put_nowait, "quit")

    threading.Thread(target=read_stdin, daemon=True).start()

    async with serve(handler, "0.0.0.0", args.port, max_size=2**22, ping_interval=20):
        log(f"Bob server on port {args.port}. Put this laptop's IP in code/bob/secrets.h. Type help.")
        reminders = asyncio.create_task(bob.reminder_loop())
        while True:
            line = await lines.get()
            if line.strip().lower() in ("quit", "exit"):
                break
            try:
                await bob.console(line)
            except Exception as exc:  # noqa: BLE001 - a bad console line must not stop the server
                print(f"error: {exc}")
        reminders.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
