# T07 — Expander and enable lines

Use [current wiring](../../../docs/HARDWARE.md). Keep SW2 open. P0 and P4–P7 are unused; P3 is the driver fault input. Only P1 (amplifier) and P2 (driver) are outputs in this revision.

1. Upload T07 and open Serial Monitor at 115200.
2. With all outputs released, measure amplifier SD and driver nSLEEP below their respective low thresholds.
3. Press `2` to toggle amplifier enable; measure SD against the fitted module's specification.
4. Press `3` to toggle driver enable; nSLEEP must reach at least 2.5 V.
5. Press `f` to check nFAULT; press `r` to release all outputs.
6. Reset and confirm the sketch releases the retained expander latch before its startup delay.

Verify the actual NPN pinout, resistor values and breakout enable straps if levels are wrong. An I²C ACK does not prove the enable voltage or motor isolation. Continue with restrained T08 only after the meter checks pass.
