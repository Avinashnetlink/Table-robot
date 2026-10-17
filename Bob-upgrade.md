# Bob — upgrade plan

Gaps, improvements, security, and AI integration for the current code. The wiring, pin map, and build phases stay in `BOB.md`, `Bob-pins.md`, and `Bob-simple.md`. This file is the next software and safety work after the robot is built and the T01–T13 tests pass.

The rule for every item below: the XIAO decides whether a wheel may turn. A laptop model may ask for a short move. It does not get a way around the motion gate in `code/bob/safety.cpp`.

## Where the code is now

| Piece | What it does today |
| --- | --- |
| `code/bob/` | Firmware `bob-1.0`. Wiring check at boot, OLED, camera stills, microphone, speaker, touch unlock, deep sleep, battery, edge sensors, bumper, and the motion gate. |
| `code/laptop/server.py` | One Python process. WebSocket on port 8765, path `/bob`. Optional faster-whisper, optional Tesseract, Windows voice, SQLite reminders. |
| `code/tests/` | One sketch per part, T01–T13. |

Voice commands that work today: time, date, one short forward or pivot, patrol on or off, stop, read a photo with Tesseract, a spoken reminder, and sleep. Any other sentence is repeated back: "I heard: …".

Motion starts only when all of these are true: a 2-second touch has unlocked drive, the battery is at least 3.40 V, the three edge sensors are healthy and see the table for that direction, the bumper is clear, the driver has no fault, Bob is not speaking, duty is within the cap (40% until the floor test lowers it), and the move is at most 400 ms forward or 250 ms for a pivot. Reverse is refused. A lost laptop link stops the wheels.

## 1. Gaps

These are differences between the written plan, the running code, and a finished desk robot.

### Plan and code disagree

| Topic | Plan in `BOB.md` | Code today |
| --- | --- | --- |
| Laptop server | FastAPI, JSON with base64 audio and JPEG | `websockets`. Binary frames tagged `A` (mic), `I` (JPEG), `P` (speaker). Text frames are small JSON commands. |
| After a photo | Raw image discarded after the reply | Every JPEG is saved in `code/laptop/photos/` until you delete it. |
| Reading a note | OCR or a vision model, and only real dates or tasks | Tesseract only, if it is installed. No vision model. No new reminder is created from a photo. |
| Study plans | Interview, learning block, and task spoken when due | Kinds `task`, `event`, `interview`, and `learning` can be stored from the console. Voice reminders are tasks only. There is no study plan. |
| Encoders | Parked, not used in version 1 | Still unwired. Distance is a timer and a duty percent, not a measured length. |
| Language model | Listed as laptop work | The last branch of `Bob._command()` speaks the transcript back. |

`code/laptop/README.md` matches the code. `BOB.md` Phase 9 and the software section still describe the earlier FastAPI shape. Update those sections when this upgrade starts, so a later change follows `server.py`.

### Behaviour gaps

- **Word match is a substring.** `has("time")` is true for any phrase that contains those letters, and `has("stop")` is true inside a longer word. "Hey Bob, stopwatch" can be heard as stop. Match whole words.
- **One listening window.** After "Hey Bob" the next utterance is the command, then listening ends. There is no follow-up turn ("what about tomorrow?").
- **Reminders only speak while Bob is connected and awake.** A due item waits. It is marked done as soon as it is spoken, including when the speaker fails and only the OLED text was sent.
- **Patrol has no voice confirmation.** "Look around" starts patrol as soon as drive is unlocked. A mis-heard word can start it.
- **No measured travel.** Without the encoders, the same 300 ms command is a different distance as the battery drops and the wheels slip.
- **Camera is a still, not a reader.** Focus, glare, and VGA size are the limit called out in Phase 10. The laptop must say "I could not read that" when the text is short or missing. That sentence exists for Tesseract. A future vision model needs the same rule.
- **Calibration can still be the defaults.** `TOUCH_IDLE`, `BATTERY_CAL`, and `EDGE_THRESHOLD_V` in `config.h` are placeholders until T05, T06, and T09 are pasted in. The boot wiring check warns. It does not block driving.

### Hardware left for later

P4–P7 on the PCF8574 are free. The N12 encoder plugs stay taped back. There is no rear cliff sensor, which is why reverse stays off. There is no IMU. A cardboard body is still Phase 12, before any printed case.

## 2. Improvements

Do the safety rows before the comfort rows. Each row names the file to change.

| Order | Improvement | Where | Done when |
| --- | --- | --- | --- |
| 1 | Shared secret on the WebSocket, and refuse a second client | `server.py`, `net.cpp`, `secrets.h` | A phone on the same Wi-Fi cannot open `/bob` and be treated as Bob. See section 3. |
| 2 | Match commands on whole words, and check "stop" before any other move word | `Bob._command()` | "stopwatch" and "sometime" do not move or stop the robot. |
| 3 | Ask before patrol | `Bob._command()` | Voice patrol starts only after a yes, and only if the touch pad is already unlocked. |
| 4 | Keep a reminder until Bob reports that the sentence was shown | `reminders` table, `reminder_loop` | A failed `say` leaves the row pending. |
| 5 | Expire photos, and stop saving them unless a flag is on | `on_binary`, `photos/` | Default matches the privacy line in `BOB.md`: keep the text result, delete the JPEG after the reply. |
| 6 | Paste real calibration and record the floor-test duty | `config.h` | Boot check no longer warns about default calibration. `DUTY_CAP_PERCENT` is the Phase 5 number, still at most 40 until you choose to raise it. |
| 7 | Bring `BOB.md` in line with `server.py` | `BOB.md` Phase 9 and the software section | The message names match the table in `code/bob/README.md`. |
| 8 | Encoder counts as a distance check, still not as permission to drive | new code after the pins are chosen | A command that asked for a few centimetres stops early if the wheel did not turn, and stops if it ran long. The edge sensors remain the cliff check. |
| 9 | A rear sensor or a documented decision to keep reverse off | hardware plus `checkStart` | Reverse stays refused until a sensor sees the table behind the wheels. |

Leave these alone until the table checklist in `BOB.md` Phase 12 has passed: raising the duty cap, enabling reverse, widening `EDGE_THRESHOLD_V` to force a dark desk to look safe, and moving the motion gate onto the laptop.

## 3. Security

Bob is a microphone, a camera, and two motors on the same network as the laptop. The motion gate stops a bad *command*. It does not stop a stranger from becoming the laptop, or from pretending to be Bob.

### What is already in place

- `secrets.h` is gitignored. `secrets.example.h` is the file that goes to GitHub. The Wi-Fi password is not in the repository while that ignore rule stays.
- The firmware refuses reverse, over-long moves, and duty above the cap, including a console `move` with a large duty or time.
- Drive stays locked until a 2-second touch on the robot. A remote command cannot unlock it.
- The microphone is not sent while the speaker is playing, or for 300 ms after.
- The camera takes a still only after a `photo` message.
- Deep sleep wakes only from the touch pad. "Hey Bob" does not wake him.
- A dropped WebSocket calls `safetyStopAll`.
- Reminder text is the only long-term text store. Microphone audio is discarded after transcription.

### What is open on a home network

The server binds `0.0.0.0` port 8765. Any device that can reach the laptop can connect to `/bob`. There is no password on that socket.

The handler stores the newest connection in `bob.ws` and still handles incoming messages from every connection. A second client can inject microphone frames and status while the real Bob is also connected. Those frames go through the same "Hey Bob" path, so a fake recording can start a move that the real robot will carry out if drive is unlocked.

The link is `ws://`, not `wss://`. On a normal home Wi-Fi, other stations on that network can read the microphone stream, the JPEGs, and the Wi-Fi-free command JSON.

Photos stay on disk. The folder is gitignored, and it is still a folder of pictures of the desk and anything Bob was asked to look at.

The touch pad is the drive lock. Anyone who can reach the robot for two seconds can unlock it. That is acceptable for a desk toy. It is a weak lock if Bob sits in a shared room.

`say` passes the sentence to Windows speech through an environment variable, which avoids putting the sentence into the PowerShell command line. Keep that pattern. Do not build a shell command out of a transcript or out of OCR text.

### Changes to make

Do this before connecting a language model that can ask for motion.

1. **A shared token.** Add `BOB_TOKEN` to `secrets.h` and to the laptop (environment variable or a local file that is gitignored). Bob sends it in the `hello` message. The server closes any connection whose hello does not match. Rotate the token if it has been on a chat log or a screenshot.
2. **One client.** If `bob.ws` is already set, close the new socket. Drop incoming audio from any socket that is not the accepted one.
3. **Bind the port on purpose.** Keep Windows Firewall on private networks only. Prefer binding to the laptop's LAN address rather than every interface, once that address is stable.
4. **Encrypt the link when the firmware stack allows it.** Use `wss://` with a pinned certificate. Until that lands, the token stops casual connections and does not stop someone already on the Wi-Fi from reading frames.
5. **Photo retention.** Default off. A `--keep-photos` flag can save them for a test. Delete files older than a day when the flag is on.
6. **Command log.** Log the command name and the move result. Do not log the Wi-Fi password, the token, or full transcripts at the default log level. `--verbose` can keep the transcript on the local console.
7. **Rate limits.** Cap `photo` and `move` to a few per minute from the voice path. The firmware already caps the length of each move.
8. **Secrets on the chip.** The XIAO image contains the Wi-Fi password. That is normal for this board. Do not publish a firmware `.bin` you built after editing `secrets.h`.

Physical work that belongs with this section: the antenna stays on the robot, the power switch is the hard off, and a failed Phase 12 row means the robot does not sit on a real table unattended. Three front sensors and a bumper are an aid, not a guarantee.

## 4. AI integration

The laptop is the place for models. The XIAO stays the camera, the microphone, the speaker, and the motion gate. Firmware flash is already about 36% of the app partition; a language model does not fit there, and a model on the chip could not see the cliff sensors any faster than the safety task already does.

### Keep this boundary

| On the XIAO | On the laptop |
| --- | --- |
| Motion gate, battery, bumper, fault, edge sensors | Speech-to-text, language model, vision, text-to-speech |
| 2-second touch unlock | Wake phrase "Hey Bob" |
| Mute the mic while speaking | Turn a transcript into one of the commands below |
| Sleep, and ignore the network while asleep | Reminders in SQLite |
| Take a JPEG only when asked | Read that JPEG, then drop it |

A model reply may use only these actions. They are the messages `bob.ino` already accepts:

| Action | Message | Model is allowed to |
| --- | --- | --- |
| Speak | `say` text, then the existing PCM path | Answer in one or two short sentences. The OLED shows about 42 characters. |
| Show | `show` | Put a name, time, or "I could not read that" on the screen. |
| Move | `move` with `forward`, `pivot_left`, or `pivot_right` | Ask once. Duty and time stay inside the firmware caps. The gate may still refuse. |
| Patrol | `patrol` | Ask only after the person confirms, and only if status says `unlocked`. |
| Look | `photo` | Ask when the person asked to read or look. One still. |
| Stop | `stop` | Use this for stop, halt, and freeze. It wins over every other action. |
| Sleep | `sleep` | Use only for an explicit good-night. |
| Remember | local SQLite insert | Store a reminder only when the person asked to be reminded, with a time they said. |

If the model returns anything else, the server speaks "I heard: …" and sends no move. That is the current fallback, and it stays.

### Speech

faster-whisper is already the speech-to-text path (`--model base.en`, or `tiny.en` when the laptop is slow). Keep the wake phrase as a fixed check in `heard()`, before any model runs. Send the model the command words only, plus the latest status JSON (battery, locked or unlocked, table sensors, patrol). Do not send it the raw microphone stream.

Half-duplex stays: `say_start` / speaker audio / `say_end`, with the mic muted on Bob for the whole reply.

### Language model

Replace the final `else` in `Bob._command()` with one function, for example `ask_model(words, status) -> action`. Two backends are enough:

1. **Local, preferred.** Ollama or another local server on the same laptop, so desk audio and photos do not leave the machine. A small instruction model is enough for time, reminders, and "what did the note say?".
2. **A cloud API, optional.** Use it only when a local model is not installed. Send the command text and, only for a "read this" request, the one JPEG. Do not send a continuous mic stream. Put the API key in an environment variable and add that variable's file to `.gitignore` if you store it in the project.

The system prompt should say: Bob is a slow desk robot; he cannot reverse; he cannot promise he will not fall; he must not invent a task from a blurry photo; he must not start patrol without a confirmation; answers are short enough to speak.

Parse the model output as JSON with a fixed set of keys. If the JSON is invalid, speak the fallback sentence and do not move.

### Vision

Phase 10 is this work. Flow:

1. The person asks to read or look.
2. The server sends `photo` and waits for one JPEG, as `take_photo()` already does.
3. Tesseract runs first. If it returns a few real words, speak them.
4. If Tesseract is empty and a vision model is configured, send that one image and ask for a short description plus any date or task that is actually visible.
5. If neither returns real text, say "I could not read that." Do not add a reminder from a guess.

Stick to VGA or smaller. The camera focus is fixed and close.

### Reminders and study plans

The table already has `due`, `kind`, and `title`. Extend it only when the voice path can fill it safely:

- Voice may add `task` with a clock time, which it already tries to do.
- `interview`, `event`, and `learning` stay console-entered until the model can show the parsed row and the person says yes.
- A learning plan is several rows (title, due, kind `learning`), not a motor route. Speaking a row must not call `move` or `patrol`.
- Keep the 10-second loop that speaks one due row while Bob is connected.

### What not to add

- Wake-word detection on the XIAO that starts motors. Sleep wake stays the touch pad.
- A model output that sets GPIO pins, PWM, or `DUTY_CAP_PERCENT`.
- Continuous video to a cloud API.
- Storing raw audio "for training" by default.
- Letting the model mark the edge sensors as optional.

## 5. Suggested order

1. Finish the hardware phases in `BOB.md` through the supervised table checklist. Software upgrades do not replace that list.
2. Section 3, items 1–3 and 5–7: token, one client, photo retention, logs, rate limit.
3. Section 2, items 2–4: whole-word commands, patrol confirmation, reminder delivery.
4. Paste calibration from the tests.
5. Align `BOB.md` with the real WebSocket messages.
6. Local speech-to-text, then a local model behind `ask_model`, with the action table above.
7. Vision on a single still, with "I could not read that" as the failure sentence.
8. Confirmed reminders and learning rows.
9. Encoders, only after the pins are free and Phase 12 has passed.

Each step should keep the existing tests green: T13 for the link, a `hey` console command for phrases, and a refused move while the touch pad is locked.
