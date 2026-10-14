# Bob — laptop server

Bob does the sensing and moving. The laptop does the thinking: speech-to-text, the "Hey Bob" check, answers, text-to-speech, reading photos and reminders. This is a single Python file, `server.py`.

![Bob full wiring](../bob/bob-wiring.png)

## Install

Python 3.10 or newer.

```
cd code\laptop
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

That is enough to connect, show text, take photos, move, patrol, and speak. On Windows, speech uses the built-in Windows voice; nothing else to install. On macOS or Linux, also `pip install pyttsx3`.

Optional extras:

| Feature | Install |
| --- | --- |
| Hear "Hey Bob" and commands | `pip install faster-whisper numpy` (downloads a speech model on first run, about 150 MB for `base.en`) |
| Read text in photos | `pip install pytesseract pillow`, and install the Tesseract program ([Windows installer](https://github.com/UB-Mannheim/tesseract/wiki)) |

## Run

```
python server.py
```

Options: `--no-stt` (do not load speech-to-text), `--model tiny.en` (faster, less accurate), `--volume 0.4` (quieter), `--duty 25` (slower voice moves), `--port 8765`, `--verbose`.

The first time, Windows Firewall asks about Python: allow it on **private** networks. Then put the laptop's IPv4 address (`ipconfig`) into `code/bob/secrets.h` as `SERVER_HOST`.

When Bob connects you see:

```
13:12:45 Bob connected, firmware bob-1.0
13:12:45 status: battery 3.95 V, table [True, True, True], sensors ok, locked, patrol False
```

## Voice commands

Say "Hey Bob", wait for the listening eyes, then a command. Or say it in one go: "Hey Bob, what time is it".

| Say | Bob |
| --- | --- |
| what time is it / what's the date | Answers |
| start patrol / look around | Patrol on (Bob must be unlocked by a 2-second touch) |
| stop / stop patrol | Stops |
| come here / forward, turn left, turn right | One short, safe move |
| read this / what is this / take a photo | Photo; reads the text if pytesseract is installed |
| remind me to call mom at 6 30 pm | Saves a reminder; Bob speaks it at that time |
| go to sleep | Says good night and sleeps |

Anything else: Bob repeats what he heard. To plug in a language model, replace the last `else` branch in `Bob._command()`.

## Console commands

Type these in the server window:

| Command | Effect |
| --- | --- |
| `say <text>` | Speak through Bob |
| `show <line1>\|<line2>` | Text on the OLED |
| `photo` / `read` | Take a photo (saved in `photos/`) / photo + read text |
| `patrol on` / `patrol off` | Patrol |
| `move forward 30 300` | One move: direction, duty %, ms |
| `stop`, `sleep`, `status` | Stop, sleep now, last status |
| `hey <words>` | Pretend Bob heard "Hey Bob <words>"; tests commands without speech-to-text |
| `remind 18:30 <text>` | Reminder today (or tomorrow if past) |
| `remind 2026-10-14 10:00 interview <text>` | Kinds: task, event, interview, learning |
| `list`, `done <id>` | Reminders |
| `quit` | Stop the server |

## Data kept on the laptop

| What | Where | Kept |
| --- | --- | --- |
| Reminders | `reminders.db` (SQLite) | Until marked done |
| Photos | `photos/` | Until you delete them |
| Microphone audio | Memory only | Discarded after transcription |

## Tested

`server.py` was run against a simulated Bob client on Windows: connect, status, microphone stream, Windows speech (16 kHz audio frames, `say_start` / `say_end`), the `hey` commands, photo request and save, moves, patrol and reminders all worked. Speech-to-text and OCR were not installed for that run.
