[Current wiring](../../../docs/HARDWARE.md) · [Circuit image](../../../images/bob-wiring.png)

# T11 — Speaker

> Follow the [revision 3 hardware/testing procedure](../../../docs/TESTING.md). Component sketches are bench diagnostics; keep motor power isolated except for restrained T08 tests.

Turns on the MAX98357A through the Q1 safe switch, plays a quiet tone and a chime over I2S, then turns the amp off.

## Wiring

| Amp pin | Connect to |
| --- | --- |
| VIN | Switched battery, with C5 100 µF + C6 100 nF to GND |
| GND | GND |
| BCLK | D6 |
| LRC | D7 |
| DIN | D10 |
| SD | Q1 collector (safe switch, PCF P1) |
| GAIN | R22 100 kΩ to VIN (3 dB, quietest) |
| OUT+ / OUT− | Speaker. **Never** connect a speaker wire to GND. |

## Keys

| Key | Action |
| --- | --- |
| `t` | 440 Hz tone, 1 s |
| `c` | Three-note chime |
| `+` / `-` | Volume up / down (starts at 10%) |

## Steps

1. Power switch on (the amp runs from the battery). Upload, open Serial Monitor at 115200.
2. A tone plays at start. Press `t` and `c`. Raise the volume with `+` until it is clear at desk distance.
3. Touch the amp chip after a minute of tones: warm is fine, hot is not.

## Pass

Clear tone and chime, no buzz between sounds, the amp stays cool.

## If it fails

| Symptom | Fix |
| --- | --- |
| Silent | SD not high while playing (run T07 key `2`), VIN not powered, or BCLK/LRC swapped. |
| Quiet and distorted | Battery low; charge it. |
| Too loud even at 10% | GAIN is not going through R22: tied straight to GND is 12 dB, left floating is 9 dB. |
| Click at every reset | Normal only if the amp is on during reset; firmware keeps it off. |
| Hum or buzz | Speaker wires near motor wires; twist the speaker pair. |
