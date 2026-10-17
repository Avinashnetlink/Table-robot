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
import asyncio
import datetime as dt
import json
import os
import pathlib
import re
import sys
import threading
import time

from websockets.asyncio.server import serve

from speech import Segmenter, Transcriber, normalize, synthesize, scale_pcm
from reminders import Reminders, parse_when
from protocol import decode_text, validate_outgoing, validate_binary, SESSION, SessionGone
from transport import RobotLink

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
        self.send_lock = asyncio.Lock()
        self.tasks: set[asyncio.Task] = set()
        self.photo_lock = asyncio.Lock()
        self.sequence = 0
        self.stt_busy = False
        self.token = args.token

    # -- sending
    async def send(self, **msg: object) -> bool:
        async with self.send_lock:
            expected = SESSION.get()
            if self.ws is None or (expected is not None and self.ws is not expected):
                raise SessionGone("robot is disconnected or session changed")
            validate_outgoing(msg)
            self.sequence += 1
            msg.update(token=self.token, seq=self.sequence)
            await asyncio.wait_for(self.ws.send(json.dumps(msg)), 2)
            return True

    async def say(self, text: str) -> bool:
        text = text[:500]
        async with self.say_lock:
            target = self.ws
            log(f"Bob says: {text}")
            await self.send(type="show", line1=text[:21], line2=text[21:42], ms=min(60000, max(3000, 80 * len(text))))
            await self.send(type="say_start")
            try:
                try:
                    pcm = scale_pcm(await synthesize(text), self.args.volume)
                except Exception as exc:
                    if target is not self.ws:
                        raise SessionGone("session changed during synthesis") from exc
                    log(f"(no voice: {exc}; text sent to OLED)")
                    return True
                if target is not self.ws:
                    raise SessionGone("session changed during synthesis")
                step = PLAY_CHUNK_SAMPLES * 2
                start = time.monotonic()
                for i in range(0, len(pcm), step):
                    if target is not self.ws:
                        raise SessionGone("session changed during playback")
                    await asyncio.wait_for(target.send(bytes([TAG_PLAY]) + pcm[i:i+step]), 2)
                    ahead = (i + min(step, len(pcm)-i)) / 2 / RATE - (time.monotonic() - start)
                    if ahead > 0:
                        await asyncio.sleep(ahead)
                return True
            finally:
                if target is self.ws and target is not None:
                    await self.send(type="say_end")

    async def take_photo(self, timeout: float = 8.0) -> pathlib.Path | None:
        async with self.photo_lock:
            self.photo_waiter = asyncio.get_running_loop().create_future()
            try:
                await self.send(type="photo")
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
            log(f"wiring check: {'no software-detected failures; bench checks required' if not problems else f'{problems} problem(s)'}")
            for item in msg.get("items", []):
                if item.get("result") != "OK" or self.args.verbose:
                    log(f"  {item.get('result'):<5} {item.get('part')}: {item.get('detail')}")
        elif t == "event":
            log(f"event: {msg.get('what')} - {msg.get('detail')}")
        elif t != "pong":
            log(f"from Bob: {msg}")

    async def on_binary(self, data: bytes) -> None:
        tag, body = validate_binary(data)
        if tag == TAG_IMAGE:
            PHOTOS.mkdir(exist_ok=True)
            path = PHOTOS / (dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".jpg")
            await asyncio.to_thread(path.write_bytes, body)
            log(f"photo saved: {path} ({len(body)} bytes)")
            if self.photo_waiter and not self.photo_waiter.done():
                self.photo_waiter.set_result(path)
        elif tag == TAG_MIC:
            utterance = self.segmenter.feed(body)
            now = time.monotonic()
            if self.segmenter.speaking and now - self.last_keep_awake > 5:
                self.last_keep_awake = now
                await self.send(type="keep_awake")
            if utterance and self.transcriber and self.transcriber.model and not self.stt_busy:
                # Never block the receive loop: Bob keeps streaming while this runs.
                self.stt_busy = True
                if not self.spawn(self.transcribe_and_handle(utterance)):
                    self.stt_busy = False

    def spawn(self, coro) -> bool:
        if len(self.tasks) >= 8:
            coro.close()
            log("Busy: command dropped")
            return False
        target = self.ws if self.ws is not None else object()
        async def scoped():
            marker = SESSION.set(target)
            try:
                await coro
            except SessionGone:
                pass
            except Exception as exc:
                log(f"command failed: {exc}")
            finally:
                SESSION.reset(marker)
        task = asyncio.create_task(scoped())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return True

    async def cancel_work(self) -> None:
        tasks = tuple(self.tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.tasks.clear()

    async def transcribe_and_handle(self, utterance: bytes) -> None:
        try:
            text = await asyncio.to_thread(self.transcriber.transcribe, utterance)
            if text:
                await self.heard(text)
        finally:
            self.stt_busy = False

    # -- conversation
    async def heard(self, text: str) -> None:
        words = normalize(text)
        log(f"heard: {text!r}")
        now = time.monotonic()
        if now < self.listening_until:
            self.listening_until = 0
            await self.send(type="listen", active=False)
            await self.command(words)
        elif words == WAKE_PHRASE or words.startswith(WAKE_PHRASE + " "):
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
        if w in ("stop patrol", "stop looking"):
            await self.send(type="patrol", on=False)
            await self.say("Patrol off.")
        elif w in ("stop", "halt", "freeze"):
            await self.send(type="stop")
            await self.say("Stopped.")
        elif w in ("patrol", "start patrol", "look around", "explore"):
            await self.send(type="patrol", on=True)
        elif w == "turn left":
            await self.send(type="move", dir="pivot_left", duty=self.args.duty, ms=200)
        elif w == "turn right":
            await self.send(type="move", dir="pivot_right", duty=self.args.duty, ms=200)
        elif w in ("forward", "come here", "move ahead"):
            await self.send(type="move", dir="forward", duty=self.args.duty, ms=300)
        elif w.startswith("remind me "):
            await self.voice_reminder(w)
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
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            await self.say("Photo saved on the laptop.")
            return
        try:
            def ocr():
                with Image.open(path) as image:
                    return " ".join(pytesseract.image_to_string(image, timeout=10).split())
            text = await asyncio.to_thread(ocr)
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
        if ap and not 1 <= h <= 12:
            await self.say("Use an hour from one to twelve with AM or PM.")
            return
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
                marker = SESSION.set(self.ws)
                try:
                    if await self.say(f"Reminder: {title}" if kind == "task" else f"{kind.capitalize()}: {title}"):
                        self.reminders.done(rid)
                except Exception as exc:
                    log(f"Reminder remains pending: {exc}")
                finally:
                    SESSION.reset(marker)

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
            ms = int(args[2]) if len(args) > 2 else (300 if args[0] == "forward" else 200)
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
    p.add_argument("--host", default="127.0.0.1", help="bind LAN IP explicitly for the robot")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--model", default="base.en", help="faster-whisper model (tiny.en is faster)")
    p.add_argument("--no-stt", action="store_true", help="do not load speech-to-text")
    p.add_argument("--volume", type=float, default=0.6, help="speech volume 0.1-1.0")
    p.add_argument("--duty", type=int, default=30, help="motor duty for voice moves, percent")
    p.add_argument("--verbose", action="store_true", help="print every status message")
    args = p.parse_args()
    args.token = os.environ.get("BOB_TOKEN", "")
    if len(args.token) < 32:
        p.error("set BOB_TOKEN to a shared random token of at least 32 characters")
    if not 0 < args.volume <= 1 or not 1 <= args.duty <= 40:
        p.error("volume must be (0,1]; duty must be 1..40")

    bob = Bob(args)

    link = RobotLink(bob)

    loop = asyncio.get_running_loop()
    lines: asyncio.Queue[str] = asyncio.Queue()

    def read_stdin() -> None:
        for line in sys.stdin:
            loop.call_soon_threadsafe(lines.put_nowait, line)
        loop.call_soon_threadsafe(lines.put_nowait, "quit")

    threading.Thread(target=read_stdin, daemon=True).start()

    async with serve(link.handle, args.host, args.port, max_size=524289, max_queue=4, compression=None, ping_interval=2, ping_timeout=2):
        log(f"Bob server on port {args.port}. Put this laptop's IP in code/bob/secrets.h. Type help.")
        reminders = asyncio.create_task(bob.reminder_loop())
        while True:
            line = await lines.get()
            if line.strip().lower() in ("quit", "exit"):
                break
            try:
                if line.strip().lower() == "stop":
                    await bob.send(type="stop")
                    await bob.cancel_work()
                else:
                    bob.spawn(bob.console(line))
            except Exception as exc:  # noqa: BLE001 - a bad console line must not stop the server
                print(f"error: {exc}")
        if bob.ws is not None:
            try:
                await bob.send(type="stop")
            except Exception:
                pass
        reminders.cancel()
        await asyncio.gather(reminders, return_exceptions=True)
        await bob.cancel_work()
    bob.reminders.db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
