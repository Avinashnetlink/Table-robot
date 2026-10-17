#!/usr/bin/env python3
"""Reproducible compile; staging uses example secrets unless --local-secrets is explicit."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
FQBN = "esp32:esp32:XIAO_ESP32S3:PSRAM=opi,CDCOnBoot=cdc"
LIBS = ["Adafruit BusIO@1.17.0", "Adafruit GFX Library@1.12.0", "Adafruit SSD1306@2.5.13",
        "WebSockets@2.6.1", "ArduinoJson@7.3.1", "VL53L0X@1.3.1", "VL6180X@1.4.0"]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--install", action="store_true", help="install pinned core and libraries")
    p.add_argument("--all", action="store_true", help="also compile the 12 component sketches")
    p.add_argument("--edge-sensor", choices=("vl6180x", "vl53l0x"), default="vl53l0x", help="family fitted to all three downward sensors (default: vl53l0x)")
    p.add_argument("--local-secrets", action="store_true", help="compile your real network credentials for flashing")
    p.add_argument("--output", type=Path, default=ROOT / "build")
    args = p.parse_args()
    if args.install:
        subprocess.run(["arduino-cli", "core", "update-index", "--additional-urls", "https://espressif.github.io/arduino-esp32/package_esp32_index.json"], check=True)
        subprocess.run(["arduino-cli", "core", "install", "esp32:esp32@3.3.12"], check=True)
        subprocess.run(["arduino-cli", "lib", "install", *LIBS], check=True)
    sources = [ROOT / "code/bob"]
    if args.all:
        sources += sorted(p for p in (ROOT / "code/tests").glob("T*") if list(p.glob("*.ino")))
    with tempfile.TemporaryDirectory(prefix="bob-source-") as tmp:
        for source in sources:
            staged = Path(tmp) / source.name
            staged.mkdir()
            for file in source.iterdir():
                if file.suffix in (".cpp", ".h", ".ino") and file.name != "secrets.h":
                    shutil.copy2(file, staged / file.name)
            example = source / "secrets.example.h"
            if example.exists():
                secret = source / "secrets.h" if args.local_secrets else example
                shutil.copy2(secret, staged / "secrets.h")
            out = args.output.resolve() / source.name
            out.mkdir(parents=True, exist_ok=True)
            flags = "-DBOB_EDGE_SENSOR=" + ("6180" if args.edge_sensor == "vl6180x" else "530")
            subprocess.run(["arduino-cli", "compile", "--fqbn", FQBN, "--warnings", "all",
                            "--build-property", "compiler.cpp.extra_flags=" + flags,
                            "--build-path", str(out / "work"), "--output-dir", str(out), str(staged)], check=True)

if __name__ == "__main__":
    main()
