# Bob laptop server

See [setup](../README.md) for installation, LAN binding and the required shared token. Run `python code/laptop/server.py --host YOUR_LAN_IP --no-stt`; remove `--no-stt` after installing optional speech recognition. Default host is localhost. The protocol is described [here](../../docs/ARCHITECTURE.md).

| Console command | Effect |
| --- | --- |
| `say text`, `show line1\|line2` | Robot speech or OLED |
| `photo`, `read` | Save JPEG, optionally OCR |
| `move forward 30 300` | Bounded motion request; local physical arming required |
| `move pivot_left`, `move pivot_right` | Default 200 ms pivot |
| `patrol on`, `patrol off` | Forward creep / stop; stops and locks at hazards |
| `stop` | Immediate stop request, cancels command work |
| `sleep`, `status` | Request sleep / print last status |
| `hey what time is it` | Test wake-phrase commands without STT |
| `remind 18:30 call home` | Local-time reminder today or tomorrow |
| `remind 2026-10-20 10:00 interview prepare` | Explicit date; task/event/interview/learning kinds |
| `list`, `done ID`, `quit` | Reminder management / server shutdown |

Voice starts with “Hey Bob”, either followed by a command or a separate utterance within 10 seconds. Motion phrases must match exactly: “forward”, “come here”, “move ahead”, “turn left”, “turn right”, “start patrol”, “patrol”, “look around”, “explore”. Negated or incidental motion words do not move the robot. Stop phrases are “stop”, “halt”, “freeze”, “stop patrol”, “stop looking”. Voice is not a physical emergency stop.

Reminders stay in `code/laptop/reminders.db`, photos in `code/laptop/photos/`; both are ignored by Git. Audio is transient memory. Successful WebSocket transmission is not proof that a user heard a reminder. `--volume` is 0–1 (exclusive of zero), `--duty` 1–40, `--model` defaults to `base.en`. No general LLM is configured; unknown speech is echoed. Keep the token private and do not port-forward this unencrypted service.
