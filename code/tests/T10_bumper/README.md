# T10 — Bumper

Prints every bumper press and release on D1.

![Bumper wiring](09-bumper.png)

## Wiring

```
3V3 ---- R14 10 kΩ ----+---- XIAO D1
                       +---- C14 100 nF ---- GND
                       +---- switch 1: NO, COM ---- GND
                       +---- switch 2: NO, COM ---- GND
```

Use the **NO** (normally open) tab and **COM** on each microswitch. Both switches in parallel.

## Steps

1. Upload, open Serial Monitor at 115200.
2. Press the left switch, release. Press the right switch, release.

## Expected output

```
Idle = high, OK. Press the left switch, then the right switch.
PRESSED  (#1) -> Bob would stop
released
PRESSED  (#2) -> Bob would stop
released
PASS if both switches each printed one press.
```

## Pass

Each press prints exactly one `PRESSED`, and idle reads high.

## If it fails

| Symptom | Fix |
| --- | --- |
| `D1 is low with nothing pressed` | A switch is on NC instead of NO, or R14 missing. |
| Several presses for one push | C14 missing. |
| One switch does nothing | Its COM is not on GND, or it is on NC. |
