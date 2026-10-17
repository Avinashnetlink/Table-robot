# Review and remaining work

## Current revision 3 changes

- Replaced the three reflective edge sensors with three matching VL6180X or VL53L0X modules through TCA9548A channels 0/1/2. Both sensor families compile from the same configuration interface.
- Added checked model identity, mux selection/read-back, range status, interrupt clear and oldest-acquisition timing. Duplicate polls cannot reacquire a surface or refresh stale data. Too near, too far, invalid, missing or stale readings inhibit motion.
- Added millimetre telemetry and a desk/air calibration analyzer. T09 now runs the production sensor code through the complete firmware; the duplicated analog sketch is gone.
- Removed the infrared devices/LED drive, analog threshold code, separate forward-ToF adapter, unused ADS library dependency, obsolete planning copies and duplicated circuit images. A single generated PNG/SVG and hardware document define the current circuit. ADS1115 remains for battery measurement because the XIAO header pins are already allocated.

## Earlier corrections retained

| Area | Implemented behavior |
| --- | --- |
| Motors | Bounded pulses, no overlapping extension, independent 5 ms guard, PWM failure fallback to GPIO-low, watchdog/setup checks |
| Safety | All three sensors required; stop purges pending moves, ends patrol and relocks; no cliff escape turn |
| Battery | Checked bounded ADC transactions, plausibility and load-sag monitoring, low-voltage lock and latched sleep request |
| Bus / PCF | 100 kHz, bounded locks/timeouts, ACK-based shadow, recovery to released outputs after uncertain writes |
| Link | Shared-token authentication, ordered commands, one connection, 400 ms heartbeat, 1500 ms lease and disconnect stop |
| Camera / audio | Explicit I²S ports, bounded PCM and capture size, PSRAM checks, echo-tail drain, stop/lock during speech/photos |
| Laptop | Modular transport/protocol/speech/reminders; bounded tasks, cancellation, photo serialization, exact motion phrases |
| Sleep / diagnostics | Safety task acknowledgment before shutdown, bounded USB status/stop commands, measurement-aware wiring reports |
| Bench tools | Motor inputs low before delays; full-power stall commands removed; no automated flashing or movement |

## Unresolved hardware limits

The assembly, delivered carrier schematics, charging behavior, motor currents, sensor mounting, stopping margin, acoustic performance and sleep current have not been physically verified. Complete [INVENTORY.md](INVENTORY.md) and [TESTING.md](TESTING.md). Motion remains disabled until measured calibration is explicitly confirmed.

Front-mounted downward sensors do not prove side/rear support during pivots. Reflective/transparent surfaces, target geometry, interference or a lower shelf can produce plausible unsafe ranges. The lightweight VL53L0X library does not include ST's full sigma estimator. There is no forward range sensor, automatic detour, encoder feedback or general LLM in this configuration.

Software deadlines share the MCU; a complete hang can leave PWM active until reset. Unattended operation requires independently engineered motor gating and sufficient coverage. Motor cutoff coasts and does not imply instant physical stopping.

Communication remains unencrypted `ws://` on a trusted isolated LAN; tokens do not prevent an on-path observer. Reminders are marked after a transmission attempt, not device/user acknowledgment. Optional STT/OCR/TTS backends and real hardware integration remain untested. See [VALIDATION.md](VALIDATION.md) for precisely which software checks passed.
