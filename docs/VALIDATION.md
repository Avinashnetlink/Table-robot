# Revision 3 validation — 17 October 2026

This revision replaces the analog edge circuit with three ToF sensors and a TCA9548A. The robot has not been connected, flashed or physically tested. `CALIBRATION_CONFIRMED=false` remains the default.

## Host checks

**PASS:** 23 Python unit/integration tests, plus seven native assertion groups across four C++ executables using ASan/UBSan and warnings-as-errors. Both VL6180X and VL53L0X edge implementations run against a fake bus.

Coverage includes all sensor combinations, bounded motor commands, stop/queue lifecycle, PWM failure fallback, battery ADC faults, mux selection, model identity, three distinct samples, stale cached/latched data, range bounds and errors, interrupt-clear failures, missing channels, startup/restart, rollover and sleep. Calibration tests reject invalid desk readings, overlapping air distances, mixed families, insufficient captures, bus faults and armed operation. Existing real loopback WebSocket tests cover authentication, ownership, heartbeat, reconnect and task cleanup.

Fake hardware cannot establish physical response times, optical reliability or electrical safety. The malformed-frame disconnect in the test log is expected.

## ESP32 builds

| Build | Result | Program bytes | Static RAM bytes |
| --- | --- | ---: | ---: |
| Three VL6180X modules | PASS | 1,044,201 | 68,944 |
| Three VL53L0X modules | PASS | 1,046,769 | 68,968 |

Final main-firmware builds completed without compiler warnings. Component-sketch compilation is still being recorded. All builds use example credentials and never flash a board. T09 is now a procedure using the production firmware, so there are 12 standalone component sketches.

Target: `esp32:esp32:XIAO_ESP32S3:PSRAM=opi,CDCOnBoot=cdc`; ESP32 Arduino core **3.3.12**. Pinned libraries: BusIO **1.17.0**, GFX **1.12.0**, SSD1306 **2.5.13**, WebSockets **2.6.1**, ArduinoJson **7.3.1**, VL53L0X **1.3.1**, VL6180X **1.4.0**. The unused ADS1X15 library dependency was removed; battery code uses checked register access. Laptop WebSockets remains **17.2**.

```sh
python tools/test.py
python tools/build_firmware.py --install --all --edge-sensor vl6180x
python tools/build_firmware.py --edge-sensor vl53l0x --output build-vl53l0x
```

The application partition limit is 3,342,336 bytes; static RAM limit is 327,680 bytes. Compiler memory reports do not measure runtime heap, PSRAM, stack headroom or latency. CI repeats the checks; no remote CI execution is claimed.

## Documentation and hardware status

The current PNG wiring diagram was visually inspected; its SVG source is supplied. Local Markdown links were checked. Superseded diagrams, planning copies and the analog edge sketch were removed.

Pending physical work: delivered carrier voltage/logic compatibility, mux branch pull-ups, channel mapping, ToF mounting/calibration and interference, current/charging measurements, stopping margin, actual camera/audio/sleep behavior, endurance and real Wi-Fi/device integration. Optional STT/OCR/TTS backends remain untested. Follow [TESTING.md](TESTING.md) and [INVENTORY.md](INVENTORY.md); software validation does not qualify the robot for unattended use.
