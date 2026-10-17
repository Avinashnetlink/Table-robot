# Hardware tests — build, upload, observe

This folder tests **real components on the XIAO**. Each T01–T13 folder contains its own `README.md`, `circuit.png` and zoomable `circuit.svg`. Open that README, build its circuit, then upload its `.ino`. **T09 uses the main firmware instead of a separate sketch.**

The root [`tests/`](../../tests/README.md) folder runs automated software checks on your laptop. Complete assembled-robot acceptance is in [`docs/TESTING.md`](../../docs/TESTING.md).

## Common setup

1. Check the [Have / Order / Tested list](../../docs/INVENTORY.md). Disconnect power before wiring. Match printed pin names, not the physical placement of symbols. All ground symbols mean the same common ground; identical power labels must be joined.
2. Use **XIAO_ESP32S3**, **OPI PSRAM**, **USB CDC enabled**, default 8 MB partition and **115200 baud**. Install the pinned core/libraries from [setup](../README.md). Open the `.ino` in the selected folder and upload using Arduino IDE.
3. Basic tests use USB power. Battery/load tests show their additional power wiring. If the robot is already assembled, leave **SW2 motor power open**, except during restrained T08 pulses. Component sketches are diagnostics, not complete robot safety firmware.
4. Starred I²C resistors are optional only when appropriate pull-ups already exist. Use the carrier voltage notes in [hardware](../../docs/HARDWARE.md); do not add every optional resistor blindly. Preserve the Sense microphone jumpers; perform the documented SD isolation before using D8/D9/D10.
5. Record results and measurements in the inventory checklist. After the component tests, restore the full circuit and main firmware and complete the [commissioning checklist](../../docs/TESTING.md).

## Choose the part to test

Every test below includes XIAO + USB. The parts column lists the additional circuit; its local diagram includes resistors, capacitors and enable wiring where required.

| Test and instructions | Additional parts / purpose | Circuit |
| --- | --- | --- |
| [T01 Camera](T01_camera/README.md) | Fitted Sense camera, PSRAM, optional Wi-Fi image | [PNG](T01_camera/circuit.png) |
| [T02 Microphone](T02_microphone/README.md) | Built-in Sense PDM mic; quiet/speech response | [PNG](T02_microphone/circuit.png) |
| [T03 I²C + mux](T03_i2c_scan/README.md) | OLED, ADC, PCF, mux + 3 VL53L0X; address scan | [PNG](T03_i2c_scan/circuit.png) |
| [T04 OLED](T04_oled/README.md) | SSD1306; text, eyes, counter | [PNG](T04_oled/circuit.png) |
| [T05 Touch](T05_touch/README.md) | Copper pad + R13; calibration | [PNG](T05_touch/circuit.png) |
| [T06 Battery ADC](T06_battery_adc/README.md) | Cell, fuse, switch, divider, ADS1115, voltmeter | [PNG](T06_battery_adc/circuit.png) |
| [T07 Enable gates](T07_pcf8574/README.md) | PCF8574 + Q1/Q2 circuits, voltmeter; no loads | [PNG](T07_pcf8574/circuit.png) |
| [T08 Motors](T08_motors/README.md) | PCF, Q2, DRV8833, motors, fused cell + kill switch | [PNG](T08_motors/circuit.png) |
| [T09 Edge sensors](T09_edge_sensors/README.md) | Full robot circuit; production firmware calibration | [PNG](T09_edge_sensors/circuit.png) |
| [T10 Bumpers](T10_bumper/README.md) | Two NO switches, pull-up and debounce capacitor | [PNG](T10_bumper/circuit.png) |
| [T11 Speaker](T11_speaker/README.md) | PCF, Q1, MAX98357A, speaker, fused cell | [PNG](T11_speaker/circuit.png) |
| [T12 Sleep / wake](T12_sleep_wake/README.md) | OLED, pad, fused cell + series current meter | [PNG](T12_sleep_wake/circuit.png) |
| [T13 Laptop link](T13_wifi_link/README.md) | Antenna, Wi-Fi LAN, laptop server | [PNG](T13_wifi_link/circuit.png) |

T01/T02 use factory board connections; T13 uses a wireless link, so those diagrams explicitly identify connections that need no jumper wires. T09 intentionally includes the full circuit. The remaining diagrams are individual bench circuits, not replacement wiring for the assembled robot.

For the complete pin-to-pin drawing and every component connection, open [the full circuit guide](../../docs/CIRCUIT.md). To regenerate images, see [tools](../../tools/README.md).
