# Bob — XIAO ESP32-S3 Sense table robot

Revision 3.1 uses **three downward-facing Robu VL53L0X modules through one TCA9548A multiplexer**. VL53L0X is now the default in both Arduino IDE and CLI builds. These replace the old reflective edge sensors; one module cannot cover all three edge positions. The bumpers provide forward contact detection.

![Full pin-to-pin schematic](images/bob-wiring.png)

[Open the full-size PNG](images/bob-wiring.png) · [Zoomable SVG](images/bob-wiring.svg) · [Individual component connections](docs/CIRCUIT.md)

| Document | Purpose |
| --- | --- |
| [Have / Order / Tested checklist](docs/INVENTORY.md) | Required parts, quantities and measurements |
| [Circuit and pin table](docs/HARDWARE.md) | Selected VL53L0X wiring, power and GPIO mapping |
| [Full pin-to-pin schematic and connection list](docs/CIRCUIT.md) | All module pins, motor/audio enables, resistors and capacitors |
| [Build and setup](code/README.md) | Select the sensor family, configure credentials and upload |
| [Tests and calibration](docs/TESTING.md) | Automated checks and staged physical commissioning |
| [Architecture](docs/ARCHITECTURE.md) | Modules, safety policy and protocol |
| [Review and limitations](docs/AUDIT.md) | Changes made and unresolved hardware limits |
| [Validation](docs/VALIDATION.md) | Recorded software checks |

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
