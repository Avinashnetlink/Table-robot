# Bob firmware v3

Use [build/setup](../README.md), [wiring](../../docs/HARDWARE.md), [testing](../../docs/TESTING.md) and [architecture/protocol](../../docs/ARCHITECTURE.md).

`config.h` is the hardware configuration and measured-calibration location. `CALIBRATION_CONFIRMED=false` deliberately prevents driving on unknown hardware. Existing real `secrets.h` files are preserved; add the token from `secrets.example.h` before networking.

A valid physical 2-second touch hold arms motion only when every input is healthy and an authenticated laptop heartbeat is fresh. A tap, explicit stop, edge, bumper, fault, stale data or low battery stops and locks motion. Patrol creeps forward and stops at the first hazard. Manual short pivots require all sensors to see table. Speech and photos stop/lock and end patrol. Touch wakes from deep sleep; voice does not.

USB commands at 115200 baud: `status`, `wiring`, `stop` plus newline. JSON telemetry includes timing, fault reasons, calibrated state, battery validity and optional range. No serial command bypasses physical arming.

Three ToF sensors are mandatory, on TCA9548A channels 0/1/2. Select one family for all three with `BOB_EDGE_SENSOR=6180` or `530`. `edge_mm`, `edge_valid` and `edge_status` replace the old analog `edge_v` telemetry. Use T09 to calibrate physical mounting and desk bands.
