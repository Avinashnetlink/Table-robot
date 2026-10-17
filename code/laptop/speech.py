"""Bounded PCM processing and optional local speech engines."""
from __future__ import annotations
import array
import asyncio
import math
import os
import sys
import tempfile
import wave
import threading
RATE = 16000

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
        try:
            await asyncio.wait_for(proc.wait(), 30)
        except BaseException:
            if proc.returncode is None:
                proc.kill()
            await proc.wait()
            raise
        if proc.returncode:
            raise RuntimeError(f"speech process exited {proc.returncode}")
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
    if sys.byteorder == "big":
        samples.byteswap()
    return samples.tobytes()


def scale_pcm(pcm: bytes, volume: float) -> bytes:
    s = array.array("h", pcm)
    if sys.byteorder == "big":
        s.byteswap()
    for i, v in enumerate(s):
        s[i] = max(-32768, min(32767, int(v * volume)))
    if sys.byteorder == "big":
        s.byteswap()
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
        if len(pcm) % 2 or len(pcm) > 1280:
            raise ValueError("invalid microphone PCM")
        s = array.array("h", pcm)
        if sys.byteorder == "big":
            s.byteswap()
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
        self.lock = threading.Lock()
        self.model = None
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            WhisperModel = None
        if WhisperModel is None:
            print("Speech-to-text off: pip install faster-whisper numpy  (console `hey ...` still works)")
            return
        print(f"Loading faster-whisper model '{model_name}' ...")
        self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
        print("Speech-to-text ready.")

    def transcribe(self, pcm: bytes) -> str:
        if self.model is None:
            return ""
        if not self.lock.acquire(blocking=False):
            return ""
        try:
            import numpy as np
            audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
            segments, _ = self.model.transcribe(audio, language="en", beam_size=1)
            return " ".join(seg.text.strip() for seg in segments).strip()
        finally:
            self.lock.release()
