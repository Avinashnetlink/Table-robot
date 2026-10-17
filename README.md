# Bob — XIAO ESP32-S3 Sense table robot

Revision 3 uses **three downward-facing VL6180X or VL53L0X modules through one TCA9548A multiplexer**. They replace the old reflective edge sensors. Choose three matching modules; a single module cannot cover all three edge positions. The bumpers provide forward contact detection.

![Current wiring](images/bob-wiring.png)

| Document | Purpose |
| --- | --- |
| [Have / Order / Tested checklist](docs/INVENTORY.md) | Required parts, quantities and measurements |
| [Circuit and pin table](docs/HARDWARE.md) | ToF/mux wiring, power, remaining component connections |
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
# Choose the family fitted to all three downward sensors:
python tools/build_firmware.py --install --all --edge-sensor vl6180x
# Alternative:
python tools/build_firmware.py --edge-sensor vl53l0x --output build-vl53l0x
```

Builds use example credentials and do not upload. Motion remains disabled by `CALIBRATION_CONFIRMED=false`. Use [setup](code/README.md) for actual upload, then [T09](code/tests/T09_edge_sensors/README.md) to measure desk/air distances with the real firmware. Mounting height and distance thresholds must change with this sensor replacement.

Camera, microphone, speech, OLED, reminders, touch, battery monitoring and short supervised motor commands remain. No general LLM is configured. There is no reverse or automatic turn at a cliff. Production qualification still requires the physical tests; software cannot prove stopping distance or protect against a completely hung MCU.
