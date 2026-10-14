# T04 — OLED screen

Shows "Bob", two eyes that blink, and a counter.

![OLED wiring](02-oled.png)

## Wiring

| OLED pin | XIAO |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SCL | D5 |
| SDA | D4 |

Power it from 3.3 V only.

## Libraries

Adafruit SSD1306 and Adafruit GFX Library.

## Steps

Upload, open Serial Monitor at 115200, watch the screen.

## Pass

`OLED found at 0x3C` is printed, the screen shows **Bob**, the eyes blink every few seconds, and the counter climbs.

## If it fails

| Symptom | Fix |
| --- | --- |
| `no OLED at 0x3C or 0x3D` | Run T03. Check the four wires. |
| Screen found but blank | Some modules are SH1106, not SSD1306: they show garbage or nothing. Buy the SSD1306 module from the product list. |
| Text shifted 2 pixels | Same: an SH1106 module. |
