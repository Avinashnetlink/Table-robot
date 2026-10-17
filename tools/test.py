#!/usr/bin/env python3
"""Host unit + local WebSocket integration tests; never opens hardware ports."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="bob-tests-") as tmp:
    for name, family in (("test_firmware", 6180), ("test_lifecycle", 6180), ("test_edges", 6180), ("test_edges", 530)):
        binary = str(Path(tmp)/f"{name}-{family}")
        sources = ["code/bob/bus.cpp", "code/bob/edges.cpp"]
        flags = [f"-DBOB_EDGE_SENSOR={family}"]
        if name != "test_edges":
            sources += ["code/bob/motion.cpp", "code/bob/pcf.cpp", "code/bob/sensors.cpp"]
        subprocess.run([os.environ.get("CXX", "c++"), "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=address,undefined", "-g", "-Itests/native/stubs", "-Icode/bob",
                        *flags, f"tests/native/{name}.cpp", *sources, "-o", binary], cwd=ROOT, check=True)
        subprocess.run([binary], check=True)
subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
