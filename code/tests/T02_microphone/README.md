# T02 — Built-in microphone

Reads the Sense board's PDM microphone (clock GPIO42, data GPIO41) and prints the sound level 20 times a second.

![XIAO pinout](00-xiao-pinout.png)

## Wiring

Nothing extra. Do **not** cut the microphone jumpers on the Sense board.

## Steps

1. Upload, then open **Tools > Serial Plotter** at 115200.
2. Stay quiet for a few seconds, then clap about 30 cm from the board.

## Expected output

The `level` line sits low (often 20–200) when quiet and jumps far higher on a clap. Every 5 s it prints:

```
# loudest peak in the last 5 s: 18542 (PASS, the mic hears you)
```

## Pass

A clap gives a clear spike, at least 10 times the quiet level.

## If it fails

| Symptom | Fix |
| --- | --- |
| `microphone did not start` | This is not the Sense board, or the expansion board is not pressed fully onto the XIAO. |
| Flat line at 0 | The microphone jumpers were cut: bridge them with solder again. |
| Very noisy when quiet | Move away from a fan or a charger. Motor noise is tested later. |
