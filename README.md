# Bob — XIAO ESP32-S3 Sense table robot

Revision 3.1 uses **three downward-facing Robu VL53L0X modules through one TCA9548A multiplexer**. VL53L0X is now the default in both Arduino IDE and CLI builds. These replace the old reflective edge sensors; one module cannot cover all three edge positions. The bumpers provide forward contact detection.

![Full pin-to-pin schematic](images/bob-wiring.png)

[Open the full-size PNG](images/bob-wiring.png) · [Zoomable SVG](images/bob-wiring.svg) · [Individual component connections](docs/CIRCUIT.md)

## Folder map

| Folder | Runs on / use |
| --- | --- |
| [`code/bob/`](code/bob/README.md) | **Robot:** main firmware uploaded to the XIAO |
| [`code/laptop/`](code/laptop/README.md) | **Laptop:** server, speech, commands and reminders |
| [`code/tests/`](code/tests/README.md) | **Real hardware tests:** T01–T13 instructions and local PNG/SVG circuits; upload one diagnostic at a time |
| [`tests/`](tests/README.md) | **Laptop software tests:** simulated firmware and server integration; no physical robot required |
| [`tools/`](tools/README.md) | **Laptop helpers:** build, run tests, capture readings, calibrate and generate drawings |
| [`images/`](docs/CIRCUIT.md) | **Complete robot circuit:** master PNG/SVG and enlarged detail sheets |
| [`docs/`](docs/TESTING.md) | **Reference and acceptance:** parts, wiring, full-robot testing, architecture and validation |
| `build/` | Generated firmware and captured test logs; created by tools, ignored by Git |
| `.github/` | Automated CI configuration for software checks and compilation |

**Build/test order:** [Have / Order checklist](docs/INVENTORY.md) → [individual parts and circuits](code/tests/README.md) → [main firmware + laptop setup](code/README.md) → [complete robot acceptance](docs/TESTING.md).

`code/tests/` covers individual component diagnostics. The root `tests/` covers automated software checks. **The complete physical robot test procedure is `docs/TESTING.md`.**

Detailed references: [pins and power](docs/HARDWARE.md), [all circuit connections](docs/CIRCUIT.md), [architecture](docs/ARCHITECTURE.md), [review/limitations](docs/AUDIT.md), [recorded validation](docs/VALIDATION.md).

## Build and check software

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r code/laptop/requirements.txt
python tools/test.py
# Selected hardware: three VL53L0X modules (also the default)
python tools/build_firmware.py --install --all --edge-sensor vl53l0x
```

Builds use example credentials and do not upload. Motion remains disabled by `CALIBRATION_CONFIRMED=false`. Use [setup](code/README.md) for actual upload, then [T09](code/tests/T09_edge_sensors/README.md) to measure desk/air distances with the real firmware. Mounting height and distance thresholds must change with this sensor replacement.

Camera, microphone, speech, OLED, reminders, touch, battery monitoring and short supervised motor commands remain. No general LLM is configured. There is no reverse or automatic turn at a cliff. Production qualification still requires the physical tests; software cannot prove stopping distance or protect against a completely hung MCU.
