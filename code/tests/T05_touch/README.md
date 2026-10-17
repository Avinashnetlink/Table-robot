[Current wiring](../../../docs/HARDWARE.md) · [Circuit image](../../../images/bob-wiring.png)

# T05 — Touch pad

> Follow the [revision 3 hardware/testing procedure](../../../docs/TESTING.md). Component sketches are bench diagnostics; keep motor power isolated except for restrained T08 tests.

Measures the copper pad on D0 untouched and touched, and prints the three numbers the full firmware needs.

## Wiring

```
XIAO D0 ---- R13 470 Ω ---- short wire ---- copper foil (about 20 × 30 mm)
```

Solder R13 within a few millimetres of the D0 pin. Keep the wire short. The foil must not touch GND, the antenna, or any metal.

## Steps

1. Upload, open Serial Monitor at 115200.
2. **Do not touch** the pad for the first 3 seconds.
3. When asked, **touch and hold** the pad with one finger for 3 seconds.
4. Copy the three printed lines into `code/bob/config.h`. Put `TOUCH_WAKE_DELTA` into T12 as well.
5. Press Enter to measure again. Repeat once the pad is mounted on the finished body, because the body changes the numbers.

## Expected output

```
Untouched: 28750
Touched:   61230
Change: +32480 (x2.13). PASS - clear change
  constexpr uint32_t TOUCH_IDLE        = 28750;
  constexpr uint32_t TOUCH_PRESS_DELTA = 16240;
  constexpr uint32_t TOUCH_WAKE_DELTA  = 12992;
```

Your numbers will differ; only the change matters.

## Pass

Touched is at least 1.2 times untouched, and the live lines print `TOUCHED` only while your finger is on the pad.

## If it fails

| Symptom | Fix |
| --- | --- |
| Touching does not raise the reading | Wire not on D0, R13 open, or the foil touches GND. |
| Weak change (below ×1.2) | Shorter wire, larger foil, foil closer to the surface of the body. |
| Random `TOUCHED` | Wire runs next to motor or speaker wires; move it. Fallback: a TTP223 module on D0. |
