# T07 — PCF8574 expander and safe switches

Toggles each PCF8574 output from the Serial Monitor so you can measure every enable line with a meter. The motor inputs are held low, so the wheels cannot turn even when the driver is awake.

![PCF8574 and safe switches](05-pcf8574.png)

## Wiring

| PCF pin | Goes to | Extra parts |
| --- | --- | --- |
| P0 | Three sensor LED cathodes (LED_K) | — |
| P1 | Q1 base through R16 100 kΩ | R15 100 kΩ to 3V3. Q1 collector to amp SD, R17 22 kΩ to 3V3 |
| P2 | Q2 base through R19 100 kΩ | R18 100 kΩ to 3V3. Q2 collector to driver SLP, R20 22 kΩ to 3V3 |
| P3 | DRV8833 FLT | R21 10 kΩ to 3V3 |
| A0, A1, A2 | GND | — |

BC547 pinout, flat face toward you, legs down: collector, base, emitter. Emitters to GND.

## Steps

1. Upload, open Serial Monitor at 115200 (line ending: none or newline, both work).
2. With everything released, measure to GND: **amp SD ≈ 0 V**, **driver SLP ≈ 0 V**. Look at the sensor LEDs through a phone camera: dark.
3. Press `2`: amp SD should read **about 2.7 V**. Press `2` again: back to 0 V.
4. Press `3`: driver SLP should read **about 3.2 V**. Press `3` again: 0 V.
5. Press `1`: the sensor LEDs glow in the phone camera. Press `1` again: dark.
6. Press `f`: the fault line reads `1 OK`.
7. Press the XIAO reset button while something is on: after reset, everything is off again.

## Pass

Every line matches the values above, and a reset turns everything off.

## If it fails

| Symptom | Fix |
| --- | --- |
| SD or SLP high when released | The BC547 is turned around (check C-B-E), or R15/R18 is missing. |
| SD or SLP stays 0 V when on | Q1/Q2 collector-emitter shorted, or R17/R20 missing. |
| SLP reads below 2.5 V when on | R20 is not 22 kΩ, or the module has a strong pulldown: try 10 kΩ for R20. |
| Fault line reads 0 | R21 missing, FLT shorted to GND, or the driver really reports a fault (overcurrent or overheat). |
| `no PCF8574` | Run T03. |
