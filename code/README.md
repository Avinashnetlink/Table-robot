# Build and setup

Use [the inventory checklist](../docs/INVENTORY.md) before ordering or connecting parts. Complete [hardware acceptance](../docs/TESTING.md) before enabling motors. Default firmware remains motion-locked.

## Reproducible command-line build

Install Arduino CLI and Python 3.12. From the repository root:

```sh
python3 tools/build_firmware.py --install --all
python3 tools/build_firmware.py --edge-sensor vl53l0x --output build-vl53l0x
```

This pins Arduino ESP32 **3.3.12**, XIAO_ESP32S3, OPI PSRAM and USB CDC; dependencies are pinned in the build script. The default 8 MB partition scheme supplies a 3 MB application partition. Verification stages a temporary source copy with **example** secrets, never the real Wi-Fi credentials. `--all` includes all 12 component sketches (T09 uses the full firmware). `--edge-sensor vl6180x` is the default for three GY-6180 modules; use `--edge-sensor vl53l0x` for three VL53L0X modules. Wrong/missing sensors keep motion locked. In Arduino IDE set `BOB_EDGE_SENSOR` to 6180 or 530 in `config.h`.

If Arduino IDE is preferred, install the same versions listed in `tools/build_firmware.py`, choose **XIAO_ESP32S3 / OPI PSRAM / USB CDC enabled / default 8 MB partition**, then open the sketch. Do not use an older generic ESP32 partition setting or the Plus pinout. ESP32 core 2.x APIs are incompatible.

## Credentials and actual upload

1. Copy `code/bob/secrets.example.h` to `code/bob/secrets.h`. Existing secrets are preserved; add `BOB_TOKEN` if missing.
2. Generate one token with `python3 -c "import secrets; print(secrets.token_hex(32))"`. Set it as `BOB_TOKEN` in that file and in the laptop environment. Set Wi-Fi credentials and `SERVER_HOST` to the laptop's LAN IPv4 address. Never commit the real file.
3. Copy **measured** touch/battery calibration values and per-sensor `EDGE_MIN_MM` / `EDGE_MAX_MM` desk bands into `code/bob/config.h`. Leave `CALIBRATION_CONFIRMED=false` until the acceptance checklist says to enable it.
4. Keep SW2 motor power off. Compile with real credentials:

```sh
python3 tools/build_firmware.py --local-secrets --edge-sensor vl6180x
arduino-cli board list
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi,CDCOnBoot=cdc \
  --input-dir build/bob --port /dev/cu.usbmodemXXXX
arduino-cli monitor --port /dev/cu.usbmodemXXXX --config baudrate=115200
```

Use `COM5` or your actual Windows port. This is an explicit upload step; neither the test suite nor build script flashes a board. Use the family matching your hardware in the actual build too. Build outputs contain credentials when compiled with `--local-secrets`; `build/` is ignored.

## Laptop

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r code/laptop/requirements.txt
export BOB_TOKEN='the-same-generated-token'
python code/laptop/server.py --host 192.168.1.50 --no-stt
```

Replace the IP with the laptop's actual LAN IP. Default binding is localhost for tests; it is not reachable by the robot until `--host` is provided. On Windows use `.venv\Scripts\Activate.ps1` and `$env:BOB_TOKEN='...'`. Allow the port only on the intended private network. `ws://` does not encrypt microphone audio, images or tokens; use a trusted isolated LAN and never expose this port to the Internet.

Optional speech input: `pip install faster-whisper numpy`, then remove `--no-stt`. The model downloads on first use. Optional output on macOS/Linux: `pip install pyttsx3` plus the system speech backend required by that package. Windows uses System.Speech. Optional OCR: `pip install pillow pytesseract` and install Tesseract. Optional dependencies are not part of the reproducible minimal test environment; verify them on the target OS.

## Sketch order and defaults

T01 camera, T02 microphone, T03 I²C, T04 OLED, T05 touch, T06 battery, T07 expander/enables, T08 restrained motors, T09 ToF calibration with full firmware, T10 bumpers, T11 speaker, T12 sleep/wake, T13 network. See their local READMEs and [updated testing procedure](../docs/TESTING.md). Component diagnostics are bench tools, not complete safety firmware.

T01/T13 have separate ignored `secrets.h` files. T13 now requires the same authentication token. T08 no longer exposes full-power stall keys. Every test now drives motor inputs low and releases possible PCF addresses before delaying.
