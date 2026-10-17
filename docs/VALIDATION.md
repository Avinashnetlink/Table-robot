# Revision 3.1 validation — 17 October 2026

The selected circuit now uses three Robu VL53L0X modules and a TCA9548A. CLI and Arduino IDE default to sensor family 530. The overview and three detailed module circuit sheets include all external pin connections and passive values. The robot has not been connected, flashed or physically tested. `CALIBRATION_CONFIRMED=false` remains the default.

## Host checks

**PASS:** 23 Python unit/integration tests, plus seven native assertion groups across four C++ executables using ASan/UBSan and warnings-as-errors. Both VL6180X and VL53L0X edge implementations run against a fake bus.

Coverage includes all sensor combinations, bounded motor commands, stop/queue lifecycle, PWM failure fallback, battery ADC faults, mux selection, model identity, three distinct samples, stale cached/latched data, range bounds and errors, interrupt-clear failures, missing channels, startup/restart, rollover and sleep. Calibration tests reject invalid desk readings, overlapping air distances, mixed families, insufficient captures, bus faults and armed operation. Existing real loopback WebSocket tests cover authentication, ownership, heartbeat, reconnect and task cleanup.

Fake hardware cannot establish physical response times, optical reliability or electrical safety. The malformed-frame disconnect in the test log is expected.

## ESP32 builds

The revision 3.1 **default CLI build (no sensor override)** passed: 1,046,769 program bytes, 68,968 static RAM bytes, no compiler warnings. The host suite above was rerun and passed. No upload was performed.

The earlier revision 3 full-build record is retained below; unchanged component sketches were not redundantly rebuilt for this documentation/default-selection update.

| Build | Result | Program bytes | Static RAM bytes |
| --- | --- | ---: | ---: |
| Three VL6180X modules | PASS | 1,044,201 | 68,944 |
| Three VL53L0X modules | PASS | 1,046,769 | 68,968 |

Both final main-firmware builds and all 12 standalone component sketches compiled successfully without compiler warnings. All builds use example credentials and never flash a board. T09 is now a procedure using the production firmware.

Target: `esp32:esp32:XIAO_ESP32S3:PSRAM=opi,CDCOnBoot=cdc`; ESP32 Arduino core **3.3.12**. Pinned libraries: BusIO **1.17.0**, GFX **1.12.0**, SSD1306 **2.5.13**, WebSockets **2.6.1**, ArduinoJson **7.3.1**, VL53L0X **1.3.1**, VL6180X **1.4.0**. The unused ADS1X15 library dependency was removed; battery code uses checked register access. Laptop WebSockets remains **17.2**.

```sh
python tools/test.py
python tools/build_firmware.py --install --all # selected VL53L0X default
python tools/build_firmware.py --edge-sensor vl6180x --output build-vl6180x # legacy adapter
```

The application partition limit is 3,342,336 bytes; static RAM limit is 327,680 bytes. Compiler memory reports do not measure runtime heap, PSRAM, stack headroom or latency. CI repeats the checks; no remote CI execution is claimed.

## Documentation and hardware status

The updated overview and all three detailed PNG circuit sheets were visually inspected; editable SVGs are supplied. Local links in all 25 Markdown files resolve. Python compile checks and git whitespace checks passed. Superseded diagrams, planning copies and the analog edge sketch were removed.

Pending physical work: delivered carrier voltage/logic compatibility, mux branch pull-ups, channel mapping, ToF mounting/calibration and interference, current/charging measurements, stopping margin, actual camera/audio/sleep behavior, endurance and real Wi-Fi/device integration. Optional STT/OCR/TTS backends remain untested. Follow [TESTING.md](TESTING.md) and [INVENTORY.md](INVENTORY.md); software validation does not qualify the robot for unattended use.


## Drawing revision 3.2 — full schematic redraw

Replaced the block-style overview and separate summary sheets with one complete pin-to-pin drawing and three detail crops of the same source. All external resistors, capacitors, transistors, motors, speaker, fuse and switches are explicit symbols. Signal wires run to their module pins; power and battery-sense flags share named nets.

The generator verified **210 component terminals**, **49 named nets** and **31 unjoined wire crossings**. It rejects wrong-net wires at terminals, unconnected terminals, touching/overlapping different-net wire segments, and wires passing through module or passive-symbol bodies. Seventeen critical sensor, motor, audio and battery nets were also checked against the project pin assignments; local Markdown links and the whitespace check passed. Full-resolution output is 5760 × 4480 PNG plus editable SVG; all views were visually inspected. The generated terminal netlist is in `docs/circuit-netlist.json`.

Firmware and electrical values were not changed in this redraw, so firmware builds and runtime tests were not repeated. Existing revision 3.1 results above still describe the software. No hardware validation or verification of the exact Robu carrier pin order/regulator circuit is claimed.

## Component test circuits and folder map — 18 October 2026

Added local `circuit.png` and `circuit.svg` to all 13 T01–T13 hardware test folders, with shorter parts/steps/pass instructions. Twelve diagrams show individual fixtures; T09 copies the full master because it uses production firmware. Camera/microphone diagrams distinguish existing board traces; Wi-Fi shows the wireless link. Added hardware-test, software-test and tools indexes and a repository folder map.

Validation: generated all diagrams, visually inspected the 12 individual layouts, decoded all 13 PNGs, parsed all 13 SVGs, confirmed T09 exactly matches the master, and verified the 12 standalone sketches plus the intentional T09 procedure. All 186 local Markdown links checked across 25 guides resolve; generator Python syntax and Git whitespace checks passed.

No functional firmware change was made; T01's printed inventory-document path was corrected. Firmware compilation and runtime suites were not repeated for these documentation/artifact changes. No hardware was connected or tested; the physical commissioning checklist remains pending.
