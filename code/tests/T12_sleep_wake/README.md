[Current wiring](../../../docs/HARDWARE.md) · [Circuit image](../../../images/bob-wiring.png)

# T12 — Sleep and touch wake

> Follow the [revision 3 hardware/testing procedure](../../../docs/TESTING.md). Component sketches are bench diagnostics; keep motor power isolated except for restrained T08 tests.

Counts down 20 seconds on the OLED, turns everything off, and deep-sleeps. Only a touch on the pad wakes it. Use it to measure the sleep current.

## Before you start

Put `TOUCH_WAKE_DELTA` from T05 into the top of `T12_sleep_wake.ino`.

## Steps

1. Unplug USB (it powers the board and hides the battery current). Put the meter in series with the battery positive, mA range.
2. Upload first over USB, then unplug and switch on from the battery.
3. Watch the OLED count down. When it goes dark, read the meter. Write the mA value in `BOB.md` Phase 7.
4. Say "Hey Bob": nothing must happen.
5. Touch the pad: the OLED shows `Hello!` and `boot 2: touch pad`.

## Expected

| State | Typical battery current |
| --- | --- |
| Awake, Wi-Fi off, OLED on | 40–80 mA |
| Asleep | about 3–4 mA (Sense board about 3 mA, safe switches 0.35 mA) |

If sleep is far higher (10 mA or more), the camera is the first suspect: the complete firmware puts an OV3660 into standby before sleeping, which this test does not.

## Pass

Bob wakes from a deliberate touch every time, does not wake by itself, and the sleep current is written down.

## If it fails

| Symptom | Fix |
| --- | --- |
| Never wakes | `TOUCH_WAKE_DELTA` too high: use a smaller value from T05. |
| Wakes by itself | `TOUCH_WAKE_DELTA` too low, or the pad wire runs near other wires. |
| Sleep current tens of mA | An LED, the amp or the driver still on: check T07 releases them. |
