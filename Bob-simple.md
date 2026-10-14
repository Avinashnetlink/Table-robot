# Bob — simple plan

Bob is a small battery robot for a table. A Seeed Studio XIAO ESP32-S3 Sense is the controller. Your laptop does the talking, reading, and reminders. Bob handles the camera, microphone, speaker, screen, touch, battery, and safe movement.

Final size comes from the real parts. The battery and wheels are the large pieces, so expect about 2.5–3.5 inches, then confirm with a cardboard model.

## Behavior

| State | What Bob does |
| --- | --- |
| Power off | The main switch is open. Nothing runs. |
| Awake | Screen on. Camera can take one photo. Microphone can listen. Speaker can answer. Wi-Fi talks to the laptop. Motors move only after the safety checks pass. |
| Listening | You say **“Hey Bob”** while he is already awake. The built-in microphone hears it. The laptop checks the words. The next sentence is the command. |
| Moving | Short, slow moves only. Forward, or a small pivot. Reverse stays off. |
| Sleep | After 60 seconds with no touch and no talk, motors stop, screen and extra parts turn off, and Bob deep-sleeps. |
| Wake | Touch or tap the copper pad. Bob wakes, reconnects Wi-Fi, and shows a greeting. |

“Hey Bob” works only while Bob is awake. In deep sleep the microphone is off, so his name will not wake him. Touch is the wake method.

One physical control: the power switch.

If Wi-Fi drops, the screen shows `Offline`. Touch and sleep still work. Motors ignore laptop commands. Bob does not invent reminders.

## What he can do

- Look at a tabletop object, a sticky note, or a laptop screen, then send one photo to the laptop.
- The laptop reads the text and answers through the speaker and the OLED.
- Store tasks, events, interviews, and learning plans on the laptop, then speak one due item when Bob is awake.
- Warn on a low battery, then stop the motors.

The laptop keeps the reminder text. It discards the photo and audio after the reply.

## Parts to buy

Confirm each Robu page on the day you order. Prices were not fixed in this plan.

| Qty | Part | Job | Where |
| --- | --- | --- | --- |
| 1 | Seeed Studio XIAO ESP32-S3 Sense | Controller, camera, microphone, Wi-Fi, charger | [Robu](https://robu.in/product/seeed-studio-xiao-esp32s3-sense-2-4ghz-wi-fi-ble-5-0-ov2640-camera-sensor-digital-microphone-battery-charge-supported-rich-interface-iot-embedded-ml/) |
| 1 | USB-C data cable | Programming | Any data cable. A charge-only cable will fail. |
| 1 | 0.96 inch 128×64 SSD1306 OLED, 4-pin I2C | Status screen | [Robu](https://robu.in/product/0-96-inch-128x64-ssd1306-iic-interface-4-pin-oled-module-blue-color-screen/) |
| 1 | Copper foil, about 20 × 30 mm | Touch pad on the body | Electronics shop |
| 1 | Protected 18650, about 2500 mAh | Battery. The cell must include a protection board. | Robu or a battery shop |
| 1 | Single 18650 holder with leads | Holds the cell | Search Robu: `18650 holder` |
| 1 | Slide or toggle switch, above 2 A | The only on/off switch | Electronics shop |
| 2 | N12 5 V 57 RPM metal-gear motor with encoder | Drive wheels | [Robu](https://robu.in/product/n12-5v-57rpm-metal-gear-motor-with-encoder/) |
| 1 | DRV8833 dual motor driver, about 2–10 V, 1.5 A | Drives both motors | [Robu](https://robu.in/product/drv8833-motor-driver-module/) |
| 2 | 34 mm rubber wheel, 3 mm D-shaft | Wheels. Buy only after the motor shaft matches. | [Robu](https://oldwp.robu.in/product/34mm-mini-car-n20-motor-wheel-rubber-small-wheel/) |
| 3 | Sharp GP2S700HCP | Front edge sensors, facing down | [Robu](https://robu.in/product/sharp-gp2s700hcp-photointerrupter-reflective-type/) |
| 2 | Extra GP2S700HCP | Spares. These tiny parts are easy to damage. | Same link |
| 1 | ADS1115 4-channel I2C ADC | Reads 3 edge sensors and battery voltage | [Robu](https://oldwp.robu.in/product/ads1115-16-bit-adc-4-channel-programmable-gain-amplifier/) |
| 1 | PCF8574T I2C I/O extension board, 3.3–5 V | Switches sensor lights, speaker amp, and motor driver. Set the A0, A1, A2 jumpers to GND. | [Robu](https://robu.in/product/pcf8574t-i2c-i-o-extension-board/) |
| 1 | MAX98357A I2S amplifier, mono | Speaker amplifier | [Robu module](https://robu.in/product/max98357-i2s-amplifier-breakout-interface-decoder-module-without-soldering/) or [Adafruit board](https://oldwp.robu.in/product/adafruit-max98357a-i2s-3w-class-d-amplifier-breakout-board/) |
| 1 | Small speaker, 4 Ω, about 1 W | Voice replies. 8 Ω is also fine, quieter. | Search Robu |
| 2 | Bumper microswitches | Front collision. Wire them together. | Electronics shop |
| 1 | Small rear skid or caster | Third contact point | Electronics or hobby shop |
| 3 | BC547 NPN transistors | Two safe switches keep the amp and motor driver off until firmware allows them. One spare. | Electronics shop |
| 10 | 470 Ω resistors | Sensor LEDs (3) and touch pad (1) | Electronics shop |
| 10 | 10 kΩ resistors | Sensor emitters (3), bumper pull-up, driver fault pull-up | Electronics shop |
| 5 | 22 kΩ resistors | Amp and driver enable pull-ups (2) | Electronics shop |
| 15 | 100 kΩ resistors | Battery divider (2), motor-input pulldowns (4), safe switches (4), amp gain (1) | Electronics shop |
| 5 | 4.7 kΩ resistors | I2C pull-ups, only if the modules have none | Electronics shop |
| 20 | 100 nF ceramic capacitors, 50 V | Decoupling, motor noise, ADC filters (11 used) | Electronics shop |
| 1 | 1000 µF electrolytic, 16 V | Across the motor supply | Electronics shop |
| 1 | 470 µF electrolytic, 16 V | Only if the 1000 µF trips the cell protection at switch-on | Electronics shop |
| 2 | 100 µF electrolytic, 16 V | Amplifier supply | Electronics shop |
| 2 | 10 µF, 16 V | XIAO 3.3 V pin | Electronics shop |
| 1 | Multimeter | Polarity, charge current, sensor calibration | — |

Every resistor and capacitor has a designator (R1–R24, C1–C14, Q1–Q2). `Bob-products.md` lists where each one goes. `images/parts/` has one wiring sheet per part.

Also buy flexible wire, heat-shrink, a small perfboard, M2 or M3 screws, and cardboard for a mock-up.

**Fallback motor, only if the N12 is too weak:** 2× N20 6 V 150 RPM with encoder. [Robu](https://oldwp.robu.in/product/n20-6v-150rpm-micro-metal-gear-motor-with-encoder/). That listing shows about 0.25 A stall current. Skip any “N20” that is about 58 mm long and 59 g.

**Later, only if a test fails:**

- TTP223 touch module, if the copper pad on D0 is unreliable.
- PCA9685, only if you later free pins for the encoders.

## Leave out

- A second camera or microphone. Use the ones on the XIAO. Leave the microphone jumpers uncut.
- VL53L0X distance sensors.
- A TP4056 or any second charger.
- A 5 V or 6 V boost board for the motors.
- 12 V or 24 V motors.
- A Raspberry Pi.
- Extra buttons.
- A microSD card. Leave that socket empty, and cut jumper J3 on the Sense board so the card's pull-ups do not reach D8 and D9.
- The 2N7000 MOSFET from the earlier plan. The PCF8574 switches the sensor LEDs directly.

## Power

```
Protected 18650
  + -- [SWITCH] --+-- XIAO BAT+
                  +-- DRV8833 VM ---- 1000 µF + 100 nF to GND
                  +-- MAX98357 VIN -- 100 µF + 100 nF to GND
                  +-- 100k -- midpoint -- 100k -- GND
                                |
                                +-- 100 nF to GND
                                +-- ADS1115 AIN3
  - --------------------------+-- all grounds, including XIAO BAT-

XIAO 3.3 V pin -- 10 µF + 100 nF to GND
```

![Bob full wiring](images/bob-wiring.png)

- Battery negative on the XIAO is the pad closer to the USB socket. Positive is the pad farther from USB. Check with a meter before soldering.
- The XIAO charges the cell when USB is plugged and the switch is on. Charge current is low, about 50–110 mA, so a 2500 mAh cell takes many hours.
- Motors run from the battery through the DRV8833, at about 3.0–4.2 V. The DRV8833 has no logic supply pin; its VCC / VM pin is the motor supply, so never wire 3.3 V to it. The 3.3 V pin powers the screen, ADC, expander, and sensor LEDs.
- All signal wires are 3.3 V.
- Put a 100 kΩ resistor from each motor input to ground so a reset cannot start a motor.
- Solder a 100 nF ceramic capacitor across each motor's two tabs.
- Warn near 3.5 V. Stop the motors near 3.4 V. Confirm both with the meter.
- Planning runtime is about 10 hours of mixed awake use, and longer in sleep. Measure it. Seeed lists about 110 mA with Wi-Fi on and about 3 mA in deep sleep for this Sense board. The camera can raise the sleep number.

Charge Bob on the bench. Unplug USB before he is allowed to drive.

## Connections

Install the antenna that comes with the board.

| XIAO pin | Connect to |
| --- | --- |
| D0 | Copper touch pad, through a 470 Ω resistor next to the pin. This pin wakes Bob. |
| D1 | Both bumper switches. 10 kΩ pull-up to 3.3 V and 100 nF to GND. Pressed = low. |
| D2 | DRV8833 AIN1, 100 kΩ to GND |
| D3 | DRV8833 AIN2, 100 kΩ to GND |
| D4 | I2C SDA: OLED, ADS1115, PCF8574 |
| D5 | I2C SCL: OLED, ADS1115, PCF8574 |
| D6 | Amplifier BCLK |
| D7 | Amplifier LRCLK |
| D8 | DRV8833 BIN1, 100 kΩ to GND |
| D9 | DRV8833 BIN2, 100 kΩ to GND |
| D10 | Amplifier DIN |
| D11 | Built-in microphone clock. Leave it. |
| D12 | Built-in microphone data. Leave it. |
| 3.3 V | OLED, ADS1115, PCF8574, sensor LEDs, pull-ups. 10 µF + 100 nF at the pin. |
| GND | Every module |
| BAT+ / BAT− | Switched battery, polarity as above |

| I2C part | Address | Use |
| --- | --- | --- |
| OLED SSD1306 | 0x3C | Screen |
| ADS1115 | 0x48 | Sensors and battery |
| PCF8574 | 0x20 | On/off enables |

The motors are on D2 / D3 and D8 / D9, not D6 / D7. D6 and D7 are the boot-log UART pins and have pull-ups at reset, so a reset could twitch a wheel.

ADS1115 inputs: AIN0 left sensor, AIN1 right sensor, AIN2 center sensor, AIN3 battery midpoint. Each input has 100 nF to ground.

Each edge sensor:

- LED: 3.3 V, then 470 Ω, then the LED, then the shared cathode line to PCF8574 P0.
- Detector: collector to 3.3 V, emitter through 10 kΩ to ground, emitter also to the ADS1115 pin with 100 nF to ground.
- One 100 nF from 3.3 V to ground on the sensor lip.
- Mount all three facing down, about 3 mm above the table, on a lip at least 25 mm in front of the wheels. Add a small shade so room light does not hit them.

PCF8574. A released pin (boot, reset, sleep) always means off:

| PCF pin | Job | How |
| --- | --- | --- |
| P0 | Turns on the three sensor LEDs | Sinks their shared cathode line directly |
| P1 | Turns on the speaker amplifier | BC547 safe switch Q1 to amp SD |
| P2 | Turns on the motor driver | BC547 safe switch Q2 to driver SLP |
| P3 | Reads the driver fault line | DRV8833 FLT, 10 kΩ pull-up. Low = fault, stop. |

Each safe switch: PCF pin with 100 kΩ to 3.3 V, then 100 kΩ to the BC547 base. Emitter to ground. Collector is the enable wire, with 22 kΩ to 3.3 V.

The PCF8574 keeps its outputs through an XIAO reset. Firmware writes 0xFF to it as the first line of `setup()` and again before sleep.

Amplifier: VIN to the switched battery with 100 µF + 100 nF to ground, GND common, speaker only between OUT+ and OUT−. Never connect a speaker wire to ground. GAIN through 100 kΩ to VIN for the lowest gain. Mute the microphone while the speaker plays.

One wiring sheet per part, with the pins and every resistor and capacitor, is in `Bob-pins.md` and `images/parts/`.

## Movement rules

The laptop may ask Bob to move. Bob’s own firmware decides.

A move is allowed only when all of these are true:

- You have held the touch pad for 2 seconds after boot.
- Battery is above the stop level.
- All three front sensors see the table.
- The bumper is released.
- Direction is forward, pivot left, or pivot right.
- Speed is at most 40% duty, and the move is at most 400 ms (250 ms for a pivot).

Any sensor fault, bumper hit, or bad reading stops both motors at once. Reverse stays off until a rear sensor is added.

Target speed on the table is about 30–40 mm/s. Set the exact duty after a floor test.

## Body

- Battery lying on its side at the bottom. Switch and skid at the rear.
- Motors on the left and right. Driver and capacitor beside them.
- Camera slightly downward, OLED on the front, speaker clear of the microphone hole.
- Copper pad on the body, away from the antenna.
- Cardboard model first. Record the real width, depth, and height. Print a case after that.

## Build order

Do these in order. Stop when a step fails.

1. XIAO alone. Run Seeed’s camera and microphone examples. Write down whether the camera says OV2640 or OV3660. Cut J3 on the Sense board.
2. OLED shows `Bob`. Touch pad gives a clear change on D0.
3. Battery polarity, charge current, and voltage reading checked with a meter.
4. Motors with wheels in the air. If one N12 stalls above about 0.4 A, change to the N20 fallback. Tape the encoder wires aside.
5. Slow moves on the floor. Set the speed cap.
6. Calibrate the three edge sensors on your real desk, then test the bumper.
7. Sleep, then wake only by touch. Measure sleep current. “Hey Bob” must do nothing while he is asleep.
8. Speaker tone, at low volume.
9. Laptop FastAPI link. Touch to wake, then “Hey Bob.”
10. One photo of a large-print note, then a laptop screen.
11. One reminder spoken and shown. A reminder never starts the motors.
12. Cardboard body, then this safety list before any free driving on a table:
    - Wheels in the air: forward and pivots work, reverse is refused.
    - Slow moves on the floor.
    - On a board with foam past the edge, he stops while the wheels are still on the board.
    - Cover or unplug one sensor: he will not start.
    - Bumper tap: he stops and does not reverse.
    - Low battery: motors stay off.
    - One slow supervised approach to a real edge, with your hand ready.

Three front sensors and a bumper reduce the chance of a fall. They do not make it impossible. Stay with him the first times he is on a table.

The longer notes, test details, and starter code are in `BOB.md`.
