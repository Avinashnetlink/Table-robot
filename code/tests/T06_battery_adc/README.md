[Current wiring](../../../docs/HARDWARE.md) · [Circuit image](../../../images/bob-wiring.png)

# T06 — Battery voltage

> Follow the [revision 3 hardware/testing procedure](../../../docs/TESTING.md). Component sketches are bench diagnostics; keep motor power isolated except for restrained T08 tests.

Reads the cell voltage through the R1/R2 divider on ADS1115 A3, compares it with your multimeter, and prints a calibration number.

## Wiring

```
VBAT (after the switch) ---- R1 100 kΩ ----+---- R2 100 kΩ ---- GND
                                           +---- C9 100 nF ---- GND
                                           +---- ADS1115 A3
ADS1115: VDD 3V3, GND, ADDR GND, SDA D4, SCL D5
```

Check battery polarity at the XIAO pads with the meter **before** soldering: negative is the pad nearer the USB socket.

## Library

No external ADC library; checked register access.

## Steps

1. Power switch on. Upload, open Serial Monitor at 115200.
2. Measure the cell (after the switch) with the meter.
3. Type the meter value, for example `3.98`, and press Enter.
4. Copy the printed `BATTERY_CAL` line into `code/bob/config.h`.

## Expected output

```
cell 3.962 V  [OK]
Meter 3.980 V, ADC 3.962 V -> error -18 mV
  constexpr float BATTERY_CAL = 1.0045;
PASS - within 50 mV
```

## Pass

Within 50 mV of the meter, or corrected by `BATTERY_CAL`. Repeat at a lower charge if you can: the error should stay small from 4.2 V down to 3.4 V.

## If it fails

| Symptom | Fix |
| --- | --- |
| `no ADS1115 at 0x48` | Run T03. ADDR must go to GND. |
| Cell reads ~0 V | Switch off, or the divider is not on A3. |
| Cell reads double or half | R1 or R2 is the wrong value; both must be 100 kΩ. |
| Error above 100 mV | Check C9 is 100 nF (not 100 µF) and the ADS1115 ground goes to the same GND as the battery. |
