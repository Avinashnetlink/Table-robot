[Current wiring](../../../docs/HARDWARE.md) · [Circuit image](../../../images/bob-wiring.png)

# T08 — Motors, wheels in the air

> Follow the [revision 3 hardware/testing procedure](../../../docs/TESTING.md). Component sketches are bench diagnostics; keep motor power isolated except for restrained T08 tests.

Runs short pulses on each motor in both directions, through the DRV8833. Every run has a time limit, and the driver is awake only during a run.

**Wheels off, or the body held so nothing can touch the table.**

## Wiring

```
VBAT ------ DRV8833 VM ---- C1 1000 µF (or 470 µF) + C2 100 nF ---- GND
GND ------- DRV8833 GND
D2 -------- AIN1 ---- R3 100 kΩ ---- GND
D3 -------- AIN2 ---- R4 100 kΩ ---- GND
D8 -------- BIN1 ---- R5 100 kΩ ---- GND
D9 -------- BIN2 ---- R6 100 kΩ ---- GND
Q2 -------- SLP      (from T07)
PCF P3 ---- FLT ---- R21 10 kΩ ---- 3V3
AOUT1/AOUT2 -- left motor,  C3 100 nF across its tabs
BOUT1/BOUT2 -- right motor, C4 100 nF across its tabs
```

No 3V3 wire to the DRV8833: its VCC / VM pin is the motor supply. Jumper J3 on the Sense board must be cut (D8 and D9). Tape the encoder wires aside.

## Keys (Serial Monitor, 115200)

| Key | Action |
| --- | --- |
| `f` | Forward 300 ms |
| `l` / `r` | Pivot left / right 250 ms |
| `a` / `A` | Left motor forward / backward 300 ms |
| `b` / `B` | Right motor forward / backward 300 ms |
| `s` / `S` | Disabled; use current-limited bench characterization |
| `+` / `-` | Duty ±5% (starts at 30%, capped at 40%) |
| `x` | Stop now |

## Steps

1. Press `a`: the left wheel turns forward (the way Bob drives). If it turns backward, swap that motor's two wires. Repeat with `b` for the right wheel.
2. Press `f`, `l`, `r`: forward, pivot left (only the right wheel turns), pivot right (only the left wheel turns).
3. Characterize startup/stall current using a current-limited supply and the motor manufacturer’s procedure. Do not hold a wheel at full battery power. Record results in [the inventory sheet](../../../docs/INVENTORY.md).
4. Reset test: press `a`, and press the XIAO reset button while the wheel turns. It must stop at once and stay stopped.

## Pass

Correct directions, measured current within the selected driver/carrier/cell/wiring budget (initial target **0.4 A** per motor), no `FAULT` message, and nothing moves at reset.

## If it fails

| Symptom | Fix |
| --- | --- |
| Nothing turns | SLP not reaching ~3.2 V (run T07), VM not connected, or switch off. |
| Right motor runs at boot, or `b` does nothing | J3 not cut: the microSD pull-ups hold D8/D9. |
| `driver FAULT` | Overcurrent or short at a motor; check the motor wires and C3/C4. |
| Stall above 0.4 A, or the motor cannot turn the wheel | Select a suitable lower-current motor after checking its actual ratings and shaft. |
| XIAO resets when a motor starts | C1 too far from VM, or a weak battery holder contact. |
