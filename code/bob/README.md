# Bob — complete firmware

The full program for Bob on the Seeed XIAO ESP32-S3 Sense. Load it only after every test in [`../tests`](../tests) has passed.

![Bob full wiring](bob-wiring.png)

![Every resistor, capacitor and transistor](bob-circuit-details.png)

## Connections

Every wire this firmware expects. The same list is at the top of [`config.h`](config.h), and each `.cpp` file starts with the wires it uses. Before wiring: cut jumper **J3** on the back of the Sense board (microSD pull-ups on D8–D10). Leave the microphone jumpers and the camera ribbon alone.

### Power

```
18650 (protected) + ---- SW1 power switch ---- VBAT
VBAT ---- XIAO BAT+ pad (farther from USB)
18650 - ---- XIAO BAT- pad (nearer USB) = GND
VBAT ---- DRV8833 VM ---- C1 1000 µF + C2 100 nF ---- GND
VBAT ---- MAX98357 VIN -- C5 100 µF  + C6 100 nF ---- GND
VBAT ---- R1 100 kΩ ---- A3 midpoint ---- R2 100 kΩ ---- GND   (C9 100 nF midpoint to GND)
XIAO 3V3 ---- C7 10 µF + C8 100 nF ---- GND
XIAO 3V3 ---- OLED, ADS1115, PCF8574, sensor LEDs and collectors, all pull-ups (never the DRV8833)
```

Wire: 22–24 AWG for battery, VM and VIN; 26–30 AWG for signals.

### XIAO pins

| XIAO | GPIO | Connects to | Extra parts |
| --- | --- | --- | --- |
| D0 | 1 | Copper touch pad | R13 470 Ω in series, at the pin |
| D1 | 2 | Both bumper switches, NO to COM to GND | R14 10 kΩ to 3V3, C14 100 nF to GND |
| D2 | 3 | DRV8833 AIN1 (left motor) | R3 100 kΩ to GND |
| D3 | 4 | DRV8833 AIN2 (left motor) | R4 100 kΩ to GND |
| D4 | 5 | I2C SDA: OLED, ADS1115, PCF8574 | R23 4.7 kΩ to 3V3 only if missing |
| D5 | 6 | I2C SCL: OLED, ADS1115, PCF8574 | R24 4.7 kΩ to 3V3 only if missing |
| D6 | 43 | MAX98357 BCLK | — |
| D7 | 44 | MAX98357 LRC | — |
| D8 | 7 | DRV8833 BIN1 (right motor) | R5 100 kΩ to GND |
| D9 | 8 | DRV8833 BIN2 (right motor) | R6 100 kΩ to GND |
| D10 | 9 | MAX98357 DIN | — |
| D11 / D12 | 42 / 41 | Built-in microphone, on the board | — |
| 3V3 / GND | — | Logic supply, common ground | C7, C8 |

### Each part

| Part | Pin → connects to |
| --- | --- |
| **OLED** (0x3C) | VCC → 3V3 · GND → GND · SDA → D4 · SCL → D5 |
| **ADS1115** (0x48) | VDD → 3V3 · GND → GND · SDA → D4 · SCL → D5 · ADDR → GND · A0 → left sensor emitter · A1 → right · A2 → center · A3 → battery midpoint |
| **PCF8574** (0x20) | VCC → 3V3 · GND → GND · SDA → D4 · SCL → D5 · A0, A1, A2 → GND · P0 → LED_K · P1 → Q1 switch · P2 → Q2 switch · P3 → DRV8833 FLT (R21 10 kΩ to 3V3) |
| **GP2S700HCP** ×3 | pad 4 anode → R7/R8/R9 470 Ω → 3V3 · pad 3 cathode → LED_K → PCF P0 · pad 2 collector → 3V3 · pad 1 emitter → ADS A0/A1/A2, R10/R11/R12 10 kΩ and C10/C11/C12 100 nF to GND · C13 100 nF 3V3 to GND on the lip |
| **Safe switch Q1** (amp) | PCF P1 → R15 100 kΩ → 3V3 · P1 → R16 100 kΩ → BC547 base · emitter → GND · collector → MAX98357 SD, R17 22 kΩ → 3V3 |
| **Safe switch Q2** (driver) | PCF P2 → R18 100 kΩ → 3V3 · P2 → R19 100 kΩ → BC547 base · emitter → GND · collector → DRV8833 SLP, R20 22 kΩ → 3V3 |
| **DRV8833** | VM → VBAT · GND → GND · AIN1 → D2 · AIN2 → D3 · BIN1 → D8 · BIN2 → D9 · SLP → Q2 · FLT → PCF P3 · AOUT1/2 → left motor (C3 100 nF across) · BOUT1/2 → right motor (C4 100 nF across). No 3V3 wire. |
| **MAX98357A** | VIN → VBAT · GND → GND · BCLK → D6 · LRC → D7 · DIN → D10 · SD → Q1 · GAIN → R22 100 kΩ → VIN · OUT+/OUT− → speaker only |
| **Bumper** ×2 | NO → D1 · COM → GND (in parallel) |
| **Touch pad** | Copper foil → short wire → R13 470 Ω → D0 |

BC547 pinout, flat face toward you, legs down: collector, base, emitter.

### Power-on wiring check

Every time Bob starts, before anything can move, the firmware checks the connections and prints a table on the Serial Monitor (115200). It also shows the first problem on the OLED and sends the table to the laptop server. The motor driver stays asleep during the check.

```
Wiring check
  PCF8574 expander     OK    answers at 0x20
  OLED screen          OK    answers at 0x3C
  ADS1115 ADC          OK    answers at 0x48
  Battery divider A3   OK    3.96 V
  Driver FLT -> P3     OK    high (no fault)
  Motor in D2/D3       OK    low at boot (R3, R4)
  Motor in D8/D9       FAIL  D8 high at boot: cut J3 on the Sense board
  Bumper D1            OK    high (released)
  Edge sensors A0-A2   OK    L 1.41 R 1.30 C 1.36 V
  Touch pad D0         OK    28811 (calibrated 28750)
  Microphone           OK    signal 412
  Speaker              OK    chime played - you should hear it
  Camera               OK    OV3660
  Wi-Fi settings       OK    MyHomeWiFi
  Calibration          OK    config.h has test values
1 problem(s). Fix every FAIL line before driving.
```

| Line | How it is checked | A FAIL means |
| --- | --- | --- |
| PCF8574 / OLED / ADS1115 | The part answers on I2C | Wire, power, or address pins; run T03 |
| Battery divider A3 | Reads the cell through R1/R2 | Switch off, or R1/R2 missing |
| Driver FLT → P3 | FLT must be high while the driver sleeps | FLT shorted to GND |
| Motor in D2/D3, D8/D9 | The pins are read as inputs before the firmware drives them; the 100 kΩ pulldowns must hold them low | J3 not cut (D8/D9), or a short to 3V3 |
| Bumper D1 | Must be high when nothing is pressed | A switch on NC, or R14 missing |
| Edge sensors | One LEDs-off / LEDs-on reading | CHECK only: Bob may not be on a surface |
| Touch pad | Reading near the calibrated `TOUCH_IDLE` | CHECK only: redo T05 |
| Microphone | 100 ms of audio is not flat | Mic jumpers cut |
| Speaker | Plays a short, quiet chime | You hear nothing: check the amp wiring (T11) |
| Camera | The camera answered at start | Ribbon not seated |
| Wi-Fi settings / Calibration | `secrets.h` and `config.h` were edited | Edit them |

## What it does

- **Wakes** on a touch of the copper pad. Shows a greeting, joins Wi-Fi, connects to the laptop.
- **Streams the microphone** to the laptop while awake. The laptop listens for "Hey Bob". The mic is muted while the speaker plays.
- **Speaks** audio the laptop sends, through the MAX98357A.
- **Shows** status and laptop text on the OLED: Wi-Fi, lock state, battery, a face.
- **Takes a photo** when the laptop asks, and sends it.
- **Moves** only when every safety check passes. **Patrols** the table: creeps forward, stops, looks again, turns away from a lost corner. Never reverses.
- **Sleeps** after 60 s with no touch and no talk. Only a touch wakes it.

## Safety design

| Layer | What it does |
| --- | --- |
| Safety task | Its own FreeRTOS task, priority above the main loop. Reads the bumper, the three edge sensors, the driver fault line and the battery about every 25 ms. It is the only code that starts a motor. |
| Motion gate | A move starts only if: unlocked by a 2-second touch, battery above 3.4 V, sensors OK, bumper released, no driver fault, not speaking, duty ≤ 40%, forward ≤ 400 ms or pivot ≤ 250 ms, and the right sensors see the table. |
| During a move | Stops at once on bumper, fault, sensor problem, speaking, or when a needed sensor loses the table. Bumper, fault and sensor problems also end patrol and lock motion until the next 2-second touch. |
| Stop timer | Every move arms a hardware one-shot timer (`esp_timer`) that stops the motors at the end, even if a task hangs. |
| Watchdog | The loop and the safety task are watched with a 5 s timeout. A hang resets the board; at reset the 100 kΩ pulldowns stop the wheels. |
| Reset | The motor pins go low first thing in `setup()`, and the PCF8574 is written 0xFF (it keeps its outputs through a reset). |
| Link lost | Patrol stops when the laptop link drops. A tap on the pad also stops patrol. |
| Reverse | Not possible: the laptop's `reverse` is refused. |

Pivot rule: a pivot needs the **center** sensor and the sensor on the side it turns toward. Patrol uses this to turn away from a corner that has lost the table: left lost → pivot right, right lost → pivot left.

## Files

| File | Job |
| --- | --- |
| `bob.ino` | `setup()`, `loop()`, laptop commands |
| `config.h` | Complete connection list, pins, addresses, calibration, limits. **Edit this.** |
| `secrets.h` | Wi-Fi name, password, laptop IP. Copy `secrets.example.h` to `secrets.h`, then edit it. This file is not pushed. |
| `safety.cpp` | The safety task, motion gate and patrol |
| `motion.cpp` | 20 kHz PWM on D2, D3, D8, D9 and the stop timer |
| `sensors.cpp` | ADS1115: edge sensors (LEDs off/on difference) and battery |
| `pcf.cpp` | PCF8574 outputs and the fault input |
| `audio.cpp` | Microphone (I2S0, PDM) and speaker (I2S1) |
| `camera.cpp` | Camera start, photo, standby before sleep |
| `display.cpp` | OLED face and text |
| `net.cpp` | Wi-Fi and the WebSocket to the laptop |
| `power.cpp` | Touch pad, deep sleep, wake |
| `bus.cpp` | One lock around the shared I2C bus |
| `wiring.cpp` | The power-on wiring check |

## Setup

1. Libraries: Adafruit SSD1306, Adafruit GFX Library, Adafruit ADS1X15, WebSockets (Markus Sattler), ArduinoJson 7. Board package esp32 by Espressif 3.x.
2. In `config.h`, paste the calibration lines from the tests:
   - `TOUCH_IDLE`, `TOUCH_PRESS_DELTA`, `TOUCH_WAKE_DELTA` from T05
   - `BATTERY_CAL` from T06
   - `EDGE_THRESHOLD_V` from T09
   - `PCF_ADDR = 0x38` if T03 found a PCF8574A
3. Copy `secrets.example.h` to `secrets.h`, then set `WIFI_SSID`, `WIFI_PASSWORD`, and `SERVER_HOST` (the laptop's IPv4 address from `ipconfig`). `secrets.h` stays on this computer.
4. Tools: **XIAO_ESP32S3**, **PSRAM: OPI PSRAM**, **USB CDC On Boot: Enabled**. Open `bob.ino`, upload.
5. Start the laptop server: `python code\laptop\server.py` (see [`../laptop/README.md`](../laptop/README.md)).

## Using Bob

| You do | Bob does |
| --- | --- |
| Switch on, or touch the pad while asleep | "Hello!", then the face. Top bar shows `WiFi` / `Offline`, `lock`, battery volts. |
| Hold the pad 2 s | "Drive unlocked". Top bar shows `drive`. Moves are now allowed. |
| Say "Hey Bob" | Eyes change to listening. Say the command next, for example "what time is it". |
| "Hey Bob, start patrol" | Top bar shows `PATROL`. Bob creeps, stops, looks, turns away from edges. |
| Tap the pad, or say "Hey Bob, stop" | Stops the motors and the patrol. |
| Leave him alone for 60 s | Screen off, deep sleep. |

In the laptop window you can also type commands; type `help` there.

## First drive checklist

Do these in order with your hand ready (from `BOB.md` Phase 12). Any failure goes back to T09.

1. Wheels in the air: `move forward`, `move pivot_left`, `move pivot_right` from the laptop run; `move reverse` is refused.
2. Floor, away from any drop: moves feel slow. Lower `DUTY_CAP_PERCENT` and `PATROL_DUTY_PERCENT` until Bob does about 30–40 mm/s.
3. A board on the floor with foam past its edge: patrol stops while the wheels are still on the board.
4. Tape over one sensor, then unplug one sensor: Bob will not start.
5. Tap the bumper during a move: stop, no reverse, motion locked.
6. Battery near 3.4 V: moves refused, `Battery low` shown.
7. One slow supervised approach to the real table edge.

## Laptop protocol

WebSocket `ws://SERVER_HOST:8765/bob`. Text frames are JSON. Binary frames start with one tag byte.

Bob → laptop:

| Message | When |
| --- | --- |
| `{"type":"hello","fw":"bob-1.0"}` | On connect |
| `{"type":"wiring","problems":0,"items":[{"part":"Bumper D1","result":"OK","detail":"high (released)"}, ...]}` | On connect: the power-on wiring check |
| `{"type":"status", "battery_v":3.92, "table":[true,true,true], "edge_v":[...], "sensors_ok":true, "bumper":false, "fault":false, "unlocked":true, "patrol":false, "moving":false, "state":"awake", "rssi":-60}` | Every 2 s |
| `{"type":"event","what":"bumper","detail":"hit","ok":false}` | Safety events, move results, touches |
| Binary `A` + PCM | Microphone, 16 kHz 16-bit mono, 40 ms per frame |
| Binary `I` + JPEG | Photo, VGA |

Laptop → Bob:

| Message | Effect |
| --- | --- |
| `{"type":"show","line1":"..","line2":"..","ms":8000}` | Text on the OLED |
| `{"type":"state","state":"thinking"}` | Face: awake, listening, thinking, speaking |
| `{"type":"listen","active":true}` | Listening face |
| Binary `P` + PCM, then `{"type":"say_end"}` | Speak. 16 kHz 16-bit mono, at most about 4 KB per frame |
| `{"type":"move","dir":"forward","duty":30,"ms":300}` | Request a move; `dir` is forward, pivot_left, pivot_right or stop |
| `{"type":"patrol","on":true}` | Patrol on / off |
| `{"type":"stop"}` | Stop motors and patrol |
| `{"type":"photo"}` | Bob sends a photo |
| `{"type":"sleep"}` | Deep sleep now |
| `{"type":"keep_awake"}` | Reset the 60 s sleep timer |
| `{"type":"ping"}` | Bob answers `pong` |

## If something is wrong

The Serial Monitor (115200) prints which parts started and every safety event, for example:

```
Bob bob-1.0, woke by touch
PCF8574 ok, OLED ok, ADS1115 ok, audio ok, camera OV3660
[move_result] no table under the sensors
[bumper] hit
```

| Symptom | Fix |
| --- | --- |
| `Motion stays disabled` | The PCF8574 or ADS1115 did not answer: run T03. |
| Every move says `locked` | Hold the pad 2 s first; check the touch numbers from T05. |
| `no table under the sensors` on the desk | Thresholds too high: redo T09 on this desk. |
| `sensor problem` / `room light` | Shade the sensors. |
| Never sleeps | The laptop keeps sending `keep_awake` while it hears noise; that is expected in a loud room. |
| Board resets during speech or motion | Low battery, or the battery holder loses contact. |
