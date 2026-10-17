# Automated software tests — run on the laptop

This folder contains software tests, including simulated firmware hardware and local WebSocket integration. It does **not** upload code or test physical components.

| Files | What they check |
| --- | --- |
| `native/test_firmware.cpp` | Motion safety policy, bus/expander/ADC failures and bounds |
| `native/test_lifecycle.cpp` | Safety lifecycle, stop/inhibit/recovery behavior |
| `native/test_edges.cpp` | Both ToF drivers, mux channels, validity and stale frames |
| `native/stubs/` | Simulated Arduino, bus and timing interfaces for laptop execution |
| `test_laptop.py` | Server protocol, authentication, commands, reconnect and local integration |
| `test_edge_calibration.py` | Offline calibration validation and rejection of unsafe samples |

From the repository root, in your Python environment:

```sh
pip install -r code/laptop/requirements.txt
python tools/test.py
```

Requires a C++17 compiler with address/undefined-behavior sanitizer support and permission to bind a local `127.0.0.1` socket. No robot or serial port is used. Passing software tests does not prove electrical wiring, stopping distance or component ratings.

**To wire and test individual parts:** [code/tests hardware index](../code/tests/README.md). **To test the assembled robot:** [physical commissioning checklist](../docs/TESTING.md). **Helper scripts:** [tools](../tools/README.md).
