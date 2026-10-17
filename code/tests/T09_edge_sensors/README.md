# T09 — ToF edge calibration using the actual firmware

The obsolete analog calibration sketch has been removed. Use the complete firmware with `CALIBRATION_CONFIRMED=false`; this exercises the same mux, drivers and status checks used during motion. No separate copy of the sensor driver is maintained.

1. Fit three Robu VL53L0X modules and the TCA9548A as shown in [hardware](../../../docs/HARDWARE.md). Use the default build or explicitly `--edge-sensor vl53l0x`. Keep SW2 open.
2. Flash using [setup](../../README.md). Confirm `edge_sensor`, three `edge_mm` readings, `edge_valid` and `edge_status` in Serial `status` JSON. Move one target at a time to verify left/right/center channel order.
3. With the restrained chassis at its intended height over the actual desk, record at least 20 samples:

```sh
python tools/bench_capture.py --port YOUR_PORT --seconds 20 --output build/desk.jsonl
```

4. Restrain the chassis with **all three sensors over the intended drop**, then capture `build/air.jsonl` the same way. Do not allow wheels to carry the chassis over an edge.
5. Generate candidate bounds:

```sh
python tools/calibrate_edges.py --desk build/desk.jsonl --air build/air.jsonl
```

The tool refuses missing/stale/bus-fault telemetry, invalid desk readings and overlapping desk/air distances. It prints `EDGE_MIN_MM` and `EDGE_MAX_MM`; it does not edit config or arm motion. Repeat for every surface, lighting condition and chassis attitude. Do not average away an unsafe surface. The 40–80 mm defaults are placeholders, not measured calibration.

Copy validated values into the selected family block in `code/bob/config.h`. Complete the remaining [commissioning tests](../../../docs/TESTING.md) before enabling motion. Moving only one sensor over a drop must stop and lock the complete robot. Three repeated polls of the same measurement must never count as three safe samples.
