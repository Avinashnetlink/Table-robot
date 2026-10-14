# Bob — product list

Buy the main list. Buy the fallback motor only if the N12 is too weak. Buy the later parts only if a test fails.

## Main list

| No. | Qty | Product name | Link |
| --- | --- | --- | --- |
| 1 | 1 | Seeed Studio XIAO ESP32-S3 Sense | https://robu.in/product/seeed-studio-xiao-esp32s3-sense-2-4ghz-wi-fi-ble-5-0-ov2640-camera-sensor-digital-microphone-battery-charge-supported-rich-interface-iot-embedded-ml/ |
| 2 | 1 | USB-C data cable | Any data cable |
| 3 | 1 | 0.96 inch 128×64 SSD1306 OLED, 4-pin I2C | https://robu.in/product/0-96-inch-128x64-ssd1306-iic-interface-4-pin-oled-module-blue-color-screen/ |
| 4 | 1 | Copper foil, about 20 × 30 mm | Electronics shop |
| 5 | 1 | Protected 18650 battery, about 2500 mAh | Robu or a battery shop |
| 6 | 1 | Single 18650 battery holder with leads | Search Robu: `18650 holder` |
| 7 | 1 | Power slide or toggle switch, above 2 A | Electronics shop |
| 8 | 2 | N12 5 V 57 RPM metal-gear motor with encoder | https://robu.in/product/n12-5v-57rpm-metal-gear-motor-with-encoder/ |
| 9 | 1 | DRV8833 dual DC motor driver module | https://robu.in/product/drv8833-motor-driver-module/ |
| 10 | 2 | 34 mm rubber wheel, 3 mm D-shaft | https://oldwp.robu.in/product/34mm-mini-car-n20-motor-wheel-rubber-small-wheel/ |
| 11 | 5 | Sharp GP2S700HCP reflective photointerrupter | https://robu.in/product/sharp-gp2s700hcp-photointerrupter-reflective-type/ |
| 12 | 1 | ADS1115 16-bit 4-channel I2C ADC module | https://oldwp.robu.in/product/ads1115-16-bit-adc-4-channel-programmable-gain-amplifier/ |
| 13 | 1 | PCF8574T I2C I/O extension board, 3.3–5 V. Set the A0, A1, A2 jumpers to GND (address 0x20). | https://robu.in/product/pcf8574t-i2c-i-o-extension-board/ |
| 14 | 1 | MAX98357A I2S amplifier breakout, mono | https://robu.in/product/max98357-i2s-amplifier-breakout-interface-decoder-module-without-soldering/ |
| 15 | 1 | Small speaker, 4 Ω, about 1 W | Search Robu |
| 16 | 2 | Bumper microswitch | Electronics shop |
| 17 | 1 | Small rear skid or caster | Hobby shop |
| 18 | 3 | BC547 NPN transistor, TO-92 | Electronics shop |
| 19 | 10 | 470 Ω resistor, ¼ W | Electronics shop |
| 20 | 10 | 10 kΩ resistor, ¼ W | Electronics shop |
| 21 | 5 | 22 kΩ resistor, ¼ W | Electronics shop |
| 22 | 15 | 100 kΩ resistor, ¼ W | Electronics shop |
| 23 | 5 | 4.7 kΩ resistor, ¼ W (I2C pull-ups, only if needed) | Electronics shop |
| 24 | 20 | 100 nF ceramic capacitor, 50 V | Electronics shop |
| 25 | 1 | 1000 µF electrolytic capacitor, 16 V | Electronics shop |
| 26 | 1 | 470 µF electrolytic capacitor, 16 V (inrush fallback) | Electronics shop |
| 27 | 2 | 100 µF electrolytic capacitor, 16 V | Electronics shop |
| 28 | 2 | 10 µF capacitor, 16 V | Electronics shop |
| 29 | 1 | Multimeter | — |
| 30 | 1 | Flexible wire: 22–24 AWG for power, 26–30 AWG for signals | Electronics shop |
| 31 | 1 | Heat-shrink tubing | Electronics shop |
| 32 | 1 | Small perfboard | Electronics shop |
| 33 | 1 | M2 or M3 screws | Electronics shop |
| 34 | 1 | Cardboard sheet | For the body mock-up |

Five GP2S700HCP parts cover three sensors and two spares. Buy the wheels only after the motor shaft is a 3 mm D-shaft.

The 2N7000 MOSFET from the earlier list is no longer used. The PCF8574 now switches the sensor LEDs directly.

The 470 µF capacitor is only for one case: Bob shuts off the moment the power switch closes. That means the cell's protection board is tripping on the 1000 µF inrush. Plug in USB to reset it, then fit the 470 µF in place of C1.

## Where each small part goes

Counts above include spares. The designators match the circuit images in `images/` and the table in `Bob-pins.md`.

| Part | Used | Designators |
| --- | --- | --- |
| BC547 | 2 | Q1 amp safe switch, Q2 driver safe switch |
| 470 Ω | 4 | R7, R8, R9 sensor LEDs; R13 touch pad |
| 10 kΩ | 5 | R10, R11, R12 sensor emitters; R14 bumper pull-up; R21 driver fault pull-up |
| 22 kΩ | 2 | R17 amp SD pull-up; R20 driver SLP pull-up |
| 100 kΩ | 11 | R1, R2 battery divider; R3–R6 motor-input pulldowns; R15, R16, R18, R19 safe switches; R22 amp gain |
| 4.7 kΩ | 0–2 | R23, R24 I2C pull-ups |
| 100 nF | 11 | C2 driver VM; C3, C4 across motors; C6 amp VIN; C8 XIAO 3V3; C9 divider; C10–C12 ADC inputs; C13 sensor lip; C14 bumper |
| 1000 µF | 1 | C1 driver VM |
| 100 µF | 1 | C5 amp VIN |
| 10 µF | 1 | C7 XIAO 3V3 |

## Fallback

| Qty | Product name | When | Link |
| --- | --- | --- | --- |
| 2 | N20 6 V 150 RPM metal-gear motor with encoder | Only if the N12 stalls above about 0.4 A or cannot move the robot | https://oldwp.robu.in/product/n20-6v-150rpm-micro-metal-gear-motor-with-encoder/ |

## Later, only if a test fails

| Qty | Product name | When |
| --- | --- | --- |
| 1 | TTP223 capacitive touch module | Copper pad on D0 does not wake Bob reliably |
| 1 | PCA9685 16-channel I2C PWM module | You add encoder feedback and need the motor pins freed |

## Names only

1. Seeed Studio XIAO ESP32-S3 Sense
2. USB-C data cable
3. 0.96 inch 128×64 SSD1306 OLED, 4-pin I2C
4. Copper foil
5. Protected 18650 battery, about 2500 mAh
6. Single 18650 battery holder
7. Power switch, above 2 A
8. N12 5 V 57 RPM metal-gear motor with encoder
9. DRV8833 dual DC motor driver module
10. 34 mm rubber wheel, 3 mm D-shaft
11. Sharp GP2S700HCP reflective photointerrupter
12. ADS1115 16-bit 4-channel I2C ADC module
13. PCF8574 I2C GPIO module
14. MAX98357A I2S amplifier breakout, mono
15. Small speaker, 4 Ω, about 1 W
16. Bumper microswitch
17. Small rear skid or caster
18. BC547 NPN transistor
19. 470 Ω resistor
20. 10 kΩ resistor
21. 22 kΩ resistor
22. 100 kΩ resistor
23. 4.7 kΩ resistor
24. 100 nF ceramic capacitor, 50 V
25. 1000 µF electrolytic capacitor, 16 V
26. 470 µF electrolytic capacitor, 16 V
27. 100 µF electrolytic capacitor, 16 V
28. 10 µF capacitor, 16 V
29. Multimeter
30. Flexible wire
31. Heat-shrink tubing
32. Small perfboard
33. M2 or M3 screws
34. Cardboard sheet
