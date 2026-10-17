# Tools — helper scripts run on your laptop

Nothing in this folder is uploaded to the XIAO. Run commands from the **repository root** in your Python environment.

| Script | Purpose | Uses real hardware? |
| --- | --- | --- |
| `test.py` | Run root `tests/`: C++ firmware simulations + Python/server tests | No; local sockets only |
| `build_firmware.py` | Compile main firmware; `--all` also compiles 12 component sketches | No; does not flash |
| `bench_capture.py` | Send `stop`, poll Serial status, save JSONL readings | **Yes**, the selected USB serial port |
| `calibrate_edges.py` | Check desk/drop JSONL and print candidate edge bounds | No; never edits config or arms motors |
| `draw_circuit.py` | Generate master PNG/SVG, detail images and circuit netlist | No |
| `draw_test_circuits.py` | Generate PNG/SVG in every T01–T13 test folder | No |

## Commands

Install laptop dependencies using [setup](../code/README.md). Building requires Arduino CLI; automated tests also require a C++17 compiler.

```sh
python tools/test.py
python tools/build_firmware.py --install --all
```

To log an attached robot running the main firmware, keep SW2 open and follow [T09](../code/tests/T09_edge_sensors/README.md). Close other Serial monitors first. Opening the serial port may reset the board.

```sh
pip install -r tools/requirements.txt
python tools/bench_capture.py --port YOUR_PORT --seconds 30 --output build/desk.jsonl
# Repeat with all sensors safely over the drop, output build/air.jsonl.
python tools/calibrate_edges.py --desk build/desk.jsonl --air build/air.jsonl
```

Replace `YOUR_PORT` with the actual `/dev/cu.usbmodem...` or `COM...` port. The capture script sends commands, so it is not a passive logger; it cannot verify physical motor isolation.

Regenerate drawings after changing their Python sources (Matplotlib is optional and needed only for drawing):

```sh
pip install matplotlib
python tools/draw_circuit.py
python tools/draw_test_circuits.py
```

The second script copies the master into T09 because T09 uses the full firmware, and draws the other 12 fixtures independently. Do not hand-edit generated images. These are wiring drawings for assembled carrier modules; confirm actual board pin labels and variant-specific straps using [the circuit guide](../docs/CIRCUIT.md).

[Hardware tests and local circuits](../code/tests/README.md) · [Software tests](../tests/README.md) · [Folder map](../README.md)
