# Verification and commissioning

## Automated checks (no robot connected)

```sh
pip install -r code/laptop/requirements.txt
python tools/test.py
python tools/build_firmware.py --install --all
python tools/build_firmware.py --edge-sensor vl53l0x --output build-vl53l0x
```

The host suite uses a C++17 compiler with ASan/UBSan and Python `unittest`. Local WebSocket integration tests bind an ephemeral **127.0.0.1** port. If an execution sandbox blocks localhost, grant that test process local socket access rather than silently skipping integration tests. CI repeats host checks and builds both firmware variants and the 12 component sketches with example secrets.

Native tests cover every edge-sensor combination, inhibit conditions, numeric limits, millisecond rollover, independent motor timer, bumper stop, active-command non-extension, stale acquisition timestamps, PWM failures, expander NACK/recovery/input protection, battery ADC NACK/short reads/timeouts and plausibility. They also exercise the real safety lifecycle and both three-sensor ToF adapters, including wrong identities, mux selection, missing hardware, out-of-band/invalid results, stale latched frames and I²C failures. Python tests cover malformed messages, motion limits and types, bounded segmentation, clipping, reminder persistence, negated commands, session isolation, photo concurrency/timeouts, command bounds, authentication, duplicate clients, reconnect, heartbeat and command delivery.

Recorded software results are in [VALIDATION.md](VALIDATION.md). **Every physical check below is pending.** No upload or hardware motion is part of the automated test run.

## Stage 0 — inventory and power off

- [ ] Fill [INVENTORY.md](INVENTORY.md); record exact board, camera, driver, ADC and amplifier variants.
- [ ] Remove cell and USB. Inspect polarity, shorts, capacitor polarity, transistor pinouts and strain relief.
- [ ] Verify external motor pulldowns, correct J3 isolation, empty SD socket and intact microphone jumpers.
- [ ] Confirm all logic pull-ups go to 3.3 V and SDA/SCL resistance is appropriate for combined modules.
- [ ] Check SW2 opens only motor VM and remains effective with USB present; label it.
- [ ] Inspect fuse/holder, wire and switch current ratings. Choose fuse from measured current, not capacity in mAh.

## Stage 1 — controller and sensors, motor power disconnected

Run the individual sketches in `code/tests/`; each now starts by forcing motor pins low and releasing the expander. T07 can enable the driver and T11 can enable audio: keep motor VM isolated. A sketch saying “PASS” reports only what its measurement actually proves.

| Test | Physical evidence required |
| --- | --- |
| T01 | Correct camera PID, PSRAM, actual viewable JPEG; board revision logged |
| T02 | Quiet vs voice signal, correct GPIO42/41; no unexplained silence/clipping |
| T03/T04 | Expected I²C addresses; visible OLED, 100 kHz scope check if available |
| T05 | Repeatable touch idle/pressed separation; copy values only after a valid calibration |
| T06 | Meter comparison at ~4.2 / 3.7 / 3.4 V; error ≤50 mV after calibration; no NaN/timeout |
| T07 | Released P1/P2 means SD/nSLEEP below their low thresholds; enabling driver exceeds 2.5 V |
| T09 | Use [full-firmware calibration](../code/tests/T09_edge_sensors/README.md); verify all three channels, desk bands and distinct air/drop readings |
| T10 | Both switches independently trigger; check correct polarity for NO or NC wiring |
| T11 | Quiet output first; clean speech, measured rail current and acceptable speaker heating |
| T12 | Current recorded, reliable deliberate touch wake, no voice wake during sleep |
| T13 | Authenticated link and message exchange; correct laptop address/token |

Repeat T09 with the chosen ToF modules at the actual mounting height, including mutual interference, black, white, glossy, patterned and actual desk surfaces, ambient lighting changes, tilted chassis, and minimum/full battery voltage. A failed surface is not approved for driving. The sensor geometry must stay fixed after calibration. If using NC series bumpers, change T10's polarity to match the wiring before testing and set the firmware option too.

## Stage 2 — controlled motor bench

- [ ] Wheels removed or robot restrained above a bench. Use a current-limited supply for initial motor/driver work. Disconnect the cell; prevent USB charging circuitry from backfeeding the supply, using a separately isolated motor VM branch where appropriate. Do not parallel power sources.
- [ ] T08 directions: `a/A/b/B` are only 300 ms; `f/l/r` are bounded short moves. Duty starts at 30%, cap 40%.
- [ ] `s/S` full-duty stall commands are disabled. Do **not** hold a wheel at full battery power to obtain a stall reading. Characterize per motor datasheet using current limiting and brief controlled pulses; record startup and stall current. Stop if heating or the supply hits its current limit.
- [ ] Confirm reset, SW2, and serial `x` stop every output. Scope PWM frequency with camera running in the complete firmware.
- [ ] Verify boot/brownout/sleep/reconnect never energizes the wheels unexpectedly.
- [ ] Measure load current and supply sag; confirm driver/carrier thermal capability and battery wiring margin.

The old “0.4 A” motor target is a conservative design budget, not a universal DRV8833 rating or a substitute for testing the actual module. Do not short an ammeter across a cell.

## Stage 3 — full firmware, restrained robot

Set calibration values and physically verify every Stage 0–2 item. Then set `CALIBRATION_CONFIRMED=true`, rebuild with local secrets, upload, connect the laptop and deliberately hold touch to arm. Re-arm only after removing each fault.

| Inject / action | Expected result | Done |
| --- | --- | :---: |
| Request move before physical hold | Refused | [ ] |
| Request duty 41, negative duration, reverse, overlong pivot | Refused; no output | [ ] |
| Repeated move requests during a pulse | No extension beyond original deadline | [ ] |
| Queue move then immediately send stop | Stops and stays locked; no delayed restart | [ ] |
| Expose each single edge sensor to air | Stops/locks; **no automatic pivot** | [ ] |
| Cover/unplug each ToF, select wrong family, unplug mux, remove ADC power, disconnect SDA | Stops/locks, invalid telemetry; reconnect does not auto-arm | [ ] |
| Stuck ADC / bus fault | Motor output low by sensor lease target; measure real elapsed time | [ ] |
| Bumper press, and a short press during ADC conversion | Motor cutoff; locked; check both switches | [ ] |
| Disconnect NC-series bumper wire if selected | Unsafe/pressed, no movement | [ ] |
| Pull nFAULT low using an appropriate test connection | Stops and locks | [ ] |
| Battery sags below 3.40 V under load | Stops; invalid/high battery reading also inhibits | [ ] |
| Battery stays below 3.30 V for 10 s | Motors off, sleep requested; verify physical current | [ ] |
| Kill laptop, Wi-Fi AP or heartbeat; keep transport open without pings | Stops and locks by link lease; each pulse still independently bounded | [ ] |
| Speech/photo request while moving | Stops and locks; no automatic patrol restart | [ ] |
| Large/malformed command, odd PCM or wrong token | Ignored/connection rejected; safety unchanged | [ ] |
| ToF reads below/above desk band, invalid status, stale or wrong channel | Stops/locks; never refreshes a lease from cached data | [ ] |
| Sleep then touch wake | Outputs off through sleep and boot; new hold required | [ ] |

USB logging can run without network. The firmware accepts newline commands `status`, `stop`, `wiring` only; it cannot arm remotely over USB.

```sh
pip install -r tools/requirements.txt
python tools/bench_capture.py --port /dev/cu.usbmodemXXXX --seconds 60 --output build/bench.jsonl
# Windows: --port COM5
```

The capture tool sends stop, polls status and writes JSONL. It fails if no samples, unexpected reported motion or a sensor cycle ≥120 ms is observed. It cannot prove actual motor voltage. Keep a logic analyzer/scope on motor inputs and measure coast travel separately.

## Stage 4 — floor and simulated edge

- [ ] On a flat floor, lower duty until measured speed is 30–40 mm/s or slower at the worst voltage/load. Adjust patrol duty below the cap too.
- [ ] Measure maximum travel after cutoff with repeated trials. All-low outputs coast.
- [ ] Use a low board on the floor with foam beyond its edge and a restraint; test all approach angles and every sensor independently.
- [ ] Confirm the downward ToF field of view reaches the boundary before the wheel danger zone, including chassis yaw/pivots; include the measured optical edge-transition offset as well as actual speed, latency and coast distance.
- [ ] Minimum 100 start/stop cycles with audio, camera, Wi-Fi and display traffic; log heap stability, maximum sensor cycle, resets and current.
- [ ] Verify main switch, motor kill, charging, idle sleep current and wake repeatability again in the final enclosure.

Only after all pass: one slow supervised raised-table approach with a restraint and an accessible motor kill switch. Front-only sensing and software-only deadlines are not sufficient for unattended operation. Record the tested surfaces and rejected surfaces in the inventory sheet.
