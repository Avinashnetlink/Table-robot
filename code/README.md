# Bob — code

Everything Bob runs, in three parts:

| Folder | What it is |
| --- | --- |
| [`tests/`](tests) | 13 small sketches. Each one checks one part of the circuit and has its own `README.md` and wiring image. |
| [`bob/`](bob) | The complete firmware for the XIAO ESP32-S3 Sense. |
| [`laptop/`](laptop) | The laptop server Bob talks to over Wi-Fi: speech, photos, reminders. |

Do the tests in order. Each one adds parts to the robot, and each one must pass before the next. The complete firmware comes last, after T13.

![Bob full wiring](bob/bob-wiring.png)

## One-time setup (Arduino IDE 2)

1. **File > Preferences > Additional boards manager URLs:** add
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
2. **Tools > Board > Boards Manager:** install **esp32 by Espressif Systems**, version 3.x.
3. **Sketch > Include Library > Manage Libraries:** install
   - Adafruit SSD1306 (say yes to Adafruit GFX Library)
   - Adafruit ADS1X15
   - WebSockets by Markus Sattler
   - ArduinoJson by Benoit Blanchon (version 7)
4. **Tools menu**, for every sketch:

| Setting | Value |
| --- | --- |
| Board | XIAO_ESP32S3 |
| PSRAM | OPI PSRAM |
| USB CDC On Boot | Enabled |
| Partition Scheme | Default with spiffs (3MB APP/1.5MB SPIFFS) |
| Port | the COM port that appears when the XIAO is plugged in |

5. Open a sketch: **File > Open** and choose the `.ino` file inside its folder. Upload. Open **Tools > Serial Monitor** at **115200** baud. Some tests also use **Tools > Serial Plotter**.

If upload fails: hold the **B** (boot) button on the XIAO, tap **R** (reset), release **B**, and upload again. Use a data USB-C cable; a charge-only cable shows no COM port.

## Files that stay on this computer

`.gitignore` keeps these off GitHub. Each one has an example file to copy:

| Copy this | To this | What you edit |
| --- | --- | --- |
| [`bob/secrets.example.h`](bob/secrets.example.h) | `bob/secrets.h` | Wi-Fi name, password, laptop IP for the complete firmware |
| [`tests/T01_camera/secrets.example.h`](tests/T01_camera/secrets.example.h) | `tests/T01_camera/secrets.h` | Optional Wi-Fi for viewing a photo in a browser. Leave empty to skip. |
| [`tests/T13_wifi_link/secrets.example.h`](tests/T13_wifi_link/secrets.example.h) | `tests/T13_wifi_link/secrets.h` | Wi-Fi name, password, laptop IP for the link test |

The laptop reminder database (`code/laptop/reminders.db`) and saved photos (`code/laptop/photos/`) are created when the server runs. They are not part of the code.

### Command line instead (optional)

```
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi code/tests/T04_oled
arduino-cli upload  --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi -p COM5 code/tests/T04_oled
arduino-cli monitor -p COM5 -c baudrate=115200
```

## Test order

| Test | Checks | Build phase in `BOB.md` | Parts that must be wired |
| --- | --- | --- | --- |
| [T01 camera](tests/T01_camera) | Camera name (OV2640 or OV3660), photos, PSRAM | 1 | XIAO, antenna |
| [T02 microphone](tests/T02_microphone) | Built-in PDM microphone | 1 | XIAO |
| [T03 I2C scan](tests/T03_i2c_scan) | Pull-ups and all three I2C parts | 2, 6 | OLED, later ADS1115 and PCF8574 |
| [T04 OLED](tests/T04_oled) | Screen shows Bob | 2 | OLED |
| [T05 touch](tests/T05_touch) | Touch pad, calibration numbers | 2 | Copper pad + R13 |
| [T06 battery](tests/T06_battery_adc) | Cell voltage, calibration number | 3 | Battery, switch, ADS1115, R1, R2, C9 |
| [T07 PCF8574](tests/T07_pcf8574) | Expander and both safe switches | 6 / 7 | PCF8574, Q1, Q2, R15–R21 |
| [T08 motors](tests/T08_motors) | Directions, stall current, fault line | 4 | DRV8833, motors, R3–R6, C1–C4 |
| [T09 edge sensors](tests/T09_edge_sensors) | Desk vs edge, thresholds | 6 | GP2S700HCP ×3, R7–R12, C10–C13 |
| [T10 bumper](tests/T10_bumper) | Both switches | 6 | Switches, R14, C14 |
| [T11 speaker](tests/T11_speaker) | Tone and chime | 8 | MAX98357A, speaker, R22, C5, C6 |
| [T12 sleep and wake](tests/T12_sleep_wake) | Deep sleep, touch wake, sleep current | 7 | Everything so far |
| [T13 Wi-Fi link](tests/T13_wifi_link) | Wi-Fi and the laptop WebSocket | 9 | Laptop server running |

## Numbers the tests give you

Four tests print lines to paste into [`bob/config.h`](bob/config.h):

| From | Paste |
| --- | --- |
| T05 | `TOUCH_IDLE`, `TOUCH_PRESS_DELTA`, `TOUCH_WAKE_DELTA` |
| T06 | `BATTERY_CAL` |
| T09 | `EDGE_THRESHOLD_V` |
| T08 / Phase 5 floor test | lower `DUTY_CAP_PERCENT` and `PATROL_DUTY_PERCENT` until Bob moves about 30–40 mm/s |

Also put `TOUCH_WAKE_DELTA` into T12 before running it.

## Safety in every sketch

- The motor pins D2, D3, D8, D9 are driven low at the very start.
- The PCF8574 is written 0xFF (everything off) at the start, because it keeps its outputs through a reset.
- Only T08 and the complete firmware ever wake the motor driver, and every run is time-limited.
