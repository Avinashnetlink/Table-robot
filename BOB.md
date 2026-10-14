# Bob

Small battery-powered table robot. The controller is a Seeed Studio XIAO ESP32-S3 Sense. Heavy work (speech, conversation, OCR, reminders) runs on a laptop. Bob only handles sensors, sound, the display, and movement that has already passed a safety check.

The body size is not fixed. It will be set by a cardboard mock-up after the parts are measured. The 18650 cell and the wheels are the large pieces, so Bob will probably land around 2.5–3.5 inches rather than 1.5 inches.

## How Bob behaves

**Awake.** Camera can take a still. The built-in microphone can listen. The speaker can answer. The OLED shows status. Motors may move only after the safety checks pass. Wi-Fi talks to the laptop.

**Listening.** While Bob is already awake, saying **“Hey Bob”** starts active listening. The built-in PDM microphone is used. The laptop decides that the phrase was heard. Bob then takes the next sentence as the command.

**Sleep.** After a configurable quiet period (start at 60 seconds) with no touch and no conversation, Bob stops the motors, finishes or drops the current action, turns the screen, amplifier, and edge-sensor lights off, and deep-sleeps.

**Wake.** A touch or tap on one copper pad wakes Bob. He reconnects Wi-Fi, shows a greeting, and waits. “Hey Bob” does nothing during deep sleep. A normal microphone cannot run speech recognition while this MCU is in deep sleep. Touch is the wake method for this version.

One physical control: the main power switch.

## Gaps to close before trusting the robot

These are the limits that change the build. Each one has a phase that proves it.

| Gap | What is true | What to do |
| --- | --- | --- |
| 1. Edge sensors are short-range | The Sharp GP2S700HCP is a reflective phototransistor. Sharp’s datasheet gives an optimal distance of about 3 mm, in a 4 × 3 × 2 mm surface-mount package. It is not a distance sensor. Three of them do not guarantee fall prevention. | Mount all three facing down, about 3 mm above the table, on a lip in front of the wheels. Shroud them from room light. Any bad reading means stop. |
| 2. Rear and turns are unprotected | Three front sensors cannot see a wheel that swings off during a spin or a reverse. | Version 1 drives forward only, in short moves. Reverse stays disabled on a table. Add a rear sensor later if reverse is required. |
| 3. Dark or shiny tables | A black surface can look like “no table”. A shiny floor beyond the edge can look like “table”. | Calibrate on the real desk in Phase 6. If the desk is too dark, use a light mat in the driving area. |
| 4. Not enough header pins | The Sense header exposes D0–D10. D11 and D12 are the built-in microphone. Camera pins stay on the expansion connector. Motors, I2S audio, I2C, touch, and a bumper already use the header. | Encoders are not wired in version 1. Edge sensors and the battery go through an ADS1115 on I2C. Lamp, amplifier, and motor-driver enables go through a PCF8574. |
| 5. Encoders cannot be read yet | The N20 listing that publishes a count is only 3 pulses per revolution. That is too coarse for accurate distance, and there is no free interrupt pin. | Park the encoder wires. Use timed, speed-capped moves that the edge sensors can stop. Closed-loop motion is a later redesign. |
| 6. “Hey Bob” is not an on-chip wake word | Espressif’s built-in wake words are not this name. The microphone is off in deep sleep. | The laptop hears “Hey Bob” from audio streamed while Bob is awake. Touch wakes him from sleep. |
| 7. Camera part number | The Robu title says OV2640. Seeed’s current wiki says that camera was discontinued and later Sense boards use the OV3660. The wiki example still covers both. | Read the marking on the camera board before any camera code. Use Seeed’s XIAO ESP32-S3 Sense camera example. |
| 8. Sleep current of the Sense board | Seeed lists about 3 mA deep sleep for the Sense board, against about 14 µA for the XIAO without the Sense expansion. The camera may draw more if it does not enter standby. | Measure sleep current in Phase 7. Put an OV3660 into software standby before sleep. If the fitted camera is an OV2640 and standby does not work, expect a much shorter idle life. |
| 9. Onboard charger is slow | Seeed’s table shows 50 mA fast charge on the XIAO ESP32-S3 column. A Sense schematic note calculates about 110 mA from a 220 kΩ set resistor. | Use only the XIAO charger. A protected 2500 mAh cell will take many hours. Measure the real current. |
| 10. No battery-voltage pin | Seeed states that no GPIO is wired to the battery. | Read a 100 kΩ + 100 kΩ divider on the ADS1115. |
| 11. Touch must be proved on this board | ESP32-S3 does have capacitive touch. D0 is GPIO1, touch channel 1. Deep sleep can wake from one touch channel. Seeed’s generic sleep samples use classic ESP32 pin numbers and must not be copied. | Phase 2 reads the copper pad. Phase 7 proves wake. If the pad is noisy, replace it with a TTP223 on the same D0 pin and use GPIO wake. |
| 12. N12 torque is unpublished here | Robu lists an N12 5 V 57 RPM motor with encoder. The page retrieved did not include stall current, torque, or shaft diameter. | Buy that motor, then measure stall current with the wheels in the air. If it is above about 0.4 A, or it cannot start the finished weight at 3.7 V, fit the N20 6 V 150 RPM fallback instead. |
| 13. Wheel diameter | A 20–25 mm wheel was not found on Robu. The confirmed N20 wheel is 34 mm with a 3 mm D-shaft. | Do not buy wheels until the motor shaft is known. Cap speed in software for whichever wheel is fitted. |
| 14. D6 / D7 are the boot UART | GPIO43 / GPIO44 have pull-ups at reset and D6 prints the ROM boot log. D2 (GPIO3) is a strapping pin only if the `STRAP_JTAG_SEL` eFuse is burned, which a stock XIAO does not have. | Motors moved to D2 / D3 and D8 / D9, held low by 100 kΩ pulldowns. D6 / D7 carry only I2S BCLK / LRC, and the amplifier is shut down during boot. If USB programming ever fails, lift the D2 wire. |
| 15. Cost | The pages used here did not show a dependable live price. | The Robu cart on purchase day is the INR total. This plan does not invent one. |
| 16. microSD pull-ups on D8–D10 | Jumper J3 on the Sense board connects the card's pull-up resistors to D8, D9 and D10. They would hold the right-motor inputs high. | Cut J3 in Phase 1. Measure D8 and D9 to 3V3: about 100 kΩ, not a few kΩ. Do not cut the microphone jumpers. |
| 17. The DRV8833 has no logic supply | The module's VCC / VM pin is the motor supply. The chip makes its own logic rail. | VM goes to the switched cell only. Never wire 3.3 V to it. |
| 18. The PCF8574 keeps its state through a reset | It stays powered when the XIAO resets or sleeps, so an enable written low stays low. | Write 0xFF as the first line of `setup()` and again before deep sleep. The 100 kΩ motor pulldowns still hold the wheels still during the reset itself. |

## What to buy, and when

Buy only the parts for the phase you are about to build. Prices and stock change; confirm each page before ordering.

### Phase 1 — board only

| Qty | Class | Part | Link |
| --- | --- | --- | --- |
| 1 | BUY | Seeed Studio XIAO ESP32-S3 Sense | https://robu.in/product/seeed-studio-xiao-esp32s3-sense-2-4ghz-wi-fi-ble-5-0-ov2640-camera-sensor-digital-microphone-battery-charge-supported-rich-interface-iot-embedded-ml/ |
| 1 | BUY | USB-C data cable | Any known-good data cable. A charge-only cable will not program the board. |

Install the antenna that comes with the XIAO. Solder headers carefully. Cut jumper J3 on the Sense board (microSD pull-ups). Do not cut the microphone jumpers.

| Qty | Class | Part | Use |
| --- | --- | --- | --- |
| 1 | BUY | 10 µF, 16 V capacitor (C7) | XIAO 3V3 pin to GND |
| 1 | BUY | 100 nF ceramic (C8) | XIAO 3V3 pin to GND |

### Phase 2 — display and touch

| Qty | Class | Part | Link |
| --- | --- | --- | --- |
| 1 | BUY | 0.96 inch, 128×64, SSD1306, 4-pin I2C OLED | https://robu.in/product/0-96-inch-128x64-ssd1306-iic-interface-4-pin-oled-module-blue-color-screen/ |
| 1 | BUY | Self-adhesive copper foil, about 20 × 30 mm | Electronics shop. One pad is enough for version 1. |
| 1 | BUY | 470 Ω resistor (R13) | In series with the touch pad, within a few mm of D0. |

### Phase 3 — battery

| Qty | Class | Part | Where |
| --- | --- | --- | --- |
| 1 | BUY | Protected 18650, about 2500 mAh, with a protection PCB | Robu or another battery seller. The cell must say protected. |
| 1 | BUY | Single 18650 holder with leads | Robu search: `18650 holder` |
| 1 | BUY | Slide or toggle switch, rated above 2 A | The only manual control. |
| 2 | BUY | 100 kΩ resistors (R1, R2) | Battery divider. |
| 1 | BUY | 100 nF ceramic (C9) | Divider midpoint to GND. |
| 1 | BUY | Multimeter | Required for charge current, polarity, and sensor calibration. |

### Phase 4 — motors

| Qty | Class | Part | Link |
| --- | --- | --- | --- |
| 2 | BUY | N12 5 V 57 RPM metal-gear motor with encoder | https://robu.in/product/n12-5v-57rpm-metal-gear-motor-with-encoder/ |
| 1 | BUY | DRV8833 dual motor module, 2–10 V, 1.5 A class | https://robu.in/product/drv8833-motor-driver-module/ |
| 2 | WAIT | 34 mm N20 rubber wheel, 3 mm D-shaft | https://oldwp.robu.in/product/34mm-mini-car-n20-motor-wheel-rubber-small-wheel/ |
| 2 | REPLACE | N20 6 V 150 RPM with encoder, only if the N12 fails Phase 4 | https://oldwp.robu.in/product/n20-6v-150rpm-micro-metal-gear-motor-with-encoder/ |
| 4 | BUY | 100 kΩ resistors (R3–R6) | One from each DRV8833 input to GND. |
| 1 | BUY | 1000 µF, 16 V electrolytic (C1) | Driver VM to GND. Keep a 470 µF in case inrush trips the cell protection. |
| 3 | BUY | 100 nF ceramic, 50 V (C2, C3, C4) | Driver VM to GND, and one across each motor's tabs. |

The N20 6 V 150 RPM listing publishes a no-load current around 30 mA, stall current around 0.25 A, and stall torque around 2.4 kg·cm, in a body about 15 × 12 × 10 mm plus a 9 mm gearbox. That is the electrical fallback. The separate listing that shows a 58 mm length and about 59 g is a larger motor. Leave that one.

Wait to buy wheels until the N12 shaft matches. The 34 mm wheel is for a 3 mm D-shaft.

### Phase 6 — edge sensors and bumper

| Qty | Class | Part | Link |
| --- | --- | --- | --- |
| 3 | BUY | Sharp GP2S700HCP reflective photointerrupter | https://robu.in/product/sharp-gp2s700hcp-photointerrupter-reflective-type/ |
| 2 | BUY | Spare GP2S700HCP if sold singly | Same part. The package is easy to overheat. |
| 1 | BUY | ADS1115 16-bit, 4-channel I2C ADC module | https://oldwp.robu.in/product/ads1115-16-bit-adc-4-channel-programmable-gain-amplifier/ |
| 1 | BUY | PCF8574T I2C I/O extension board, 3.3–5 V | https://robu.in/product/pcf8574t-i2c-i-o-extension-board/ . Set the A0, A1, A2 jumpers to GND (0x20). These boards usually carry 10 kΩ SDA/SCL pull-ups; T03 tells you if R23/R24 are still needed. |
| 3 | BUY | BC547 (or similar NPN) (Q1, Q2) | Amp and driver safe switches. One spare. |
| 3 | BUY | 470 Ω (R7–R9) | One per sensor LED. |
| 3 | BUY | 10 kΩ (R10–R12) | Sensor emitter resistors. Change after calibration if a channel saturates. |
| 4 | BUY | 100 kΩ (R15, R16, R18, R19) | Safe-switch pull-ups and base resistors. |
| 2 | BUY | 22 kΩ (R17, R20) | Amp SD and driver SLP pull-ups. |
| 2 | BUY | 10 kΩ (R14, R21) | Bumper pull-up and driver FLT pull-up. |
| 5 | BUY | 100 nF ceramic (C10–C14) | ADC inputs A0–A2, 3V3 at the sensor lip, bumper line. |
| 2 | OPTIONAL | 4.7 kΩ (R23, R24) | I2C pull-ups, only if the modules have none. |
| 2 | BUY | Bumper microswitches, wired in parallel | One GPIO. Either switch means stop. |
| 1 | BUY | Small rear skid (wire skid or a tiny caster) | Shop part. |

### Phase 8 — voice

| Qty | Class | Part | Link |
| --- | --- | --- | --- |
| 1 | BUY | Mono MAX98357A I2S amplifier breakout | Confirm it is the mono part: https://robu.in/product/max98357-i2s-amplifier-breakout-interface-decoder-module-without-soldering/ or the documented Adafruit board https://oldwp.robu.in/product/adafruit-max98357a-i2s-3w-class-d-amplifier-breakout-board/ |
| 1 | BUY | Small speaker, 4 Ω, about 1 W | Search Robu. An 8 Ω speaker also works, at lower volume. |

| 1 | BUY | 100 kΩ (R22) | GAIN to VIN, 3 dB. |
| 1 | BUY | 100 µF, 16 V electrolytic (C5) | Amp VIN to GND. |
| 1 | BUY | 100 nF ceramic (C6) | Amp VIN to GND. |

The Adafruit listing states 2.7–5.5 V supply and about 3.2 W into 4 Ω at 5 V, 10% THD. On one lithium cell the supply is lower, so the sound is quieter. Use the lowest gain: 3 dB is GAIN tied to VIN through 100 kΩ (R22); 6 dB is GAIN tied straight to VIN.

### Do not buy

| Part | Why |
| --- | --- |
| External camera or microphone | Use the Sense camera and the PDM mic. Leave the mic jumpers intact. |
| VL53L0X | Replaced by the three GP2S700HCP sensors. |
| TP4056, or any second charger | The XIAO already charges the cell. Two chargers on one cell is unsafe. |
| 5 V or 6 V boost module for the motors | The cell voltage is the motor supply. A boost adds sag and noise. |
| 12 V or 24 V motors | Wrong for one cell. |
| The 58 mm / 59 g motor sold under an N20 name | Too large for this body. |
| Raspberry Pi | The XIAO is the controller. |
| Extra buttons | Touch, voice, and the power switch are the controls. |
| microSD card | D8, D9, and D10 are reused. Leave the socket empty and cut J3. |
| 2N7000 MOSFET | Its gate threshold can reach 3 V, too close to 3.3 V. PCF8574 P0 sinks the sensor LEDs directly. |
| TTP223 touch module | Optional later, and only if the copper pad on D0 fails Phase 2 or Phase 7. |
| PCA9685 | Optional later, only if encoder feedback is added and the motor pins must move. |

### Also buy for assembly

Flexible wire (22–24 AWG for battery, VM and VIN; 26–30 AWG for signals), heat-shrink, a small perfboard, M2/M3 screws, motor brackets or tape for the first chassis, and a cardboard sheet for the mock-up.

The full list with spares and every designator is in `Bob-products.md`.

## Compatibility

| Item | Result |
| --- | --- |
| XIAO logic | 3.3 V. Do not put 5 V on a GPIO, the OLED logic, the ADC, or the amplifier logic. |
| OLED | 4-pin I2C module, SSD1306, address usually 0x3C. Power it from 3.3 V. |
| ADS1115 | 2.0–5.5 V. Power it from 3.3 V so I2C stays at 3.3 V. Default address 0x48 with ADDR at GND. |
| PCF8574 | Same I2C bus. Address 0x20 when A0–A2 are at GND; a PCF8574A answers at 0x38. Sinks 25 mA per pin, enough for the three sensor LEDs (about 13 mA) on P0. Keeps its outputs through an XIAO reset. |
| DRV8833 | Motor supply from the cell (about 3.0–4.2 V), inside the module’s 2–10 V range. No logic supply pin: the module's VCC / VM is the motor supply. Inputs are held low by 100 kΩ pulldowns. nSLEEP needs above 2.5 V to wake; the safe switch gives about 3.2 V. |
| N12 5 V 57 RPM | Speed class matches a table robot on one cell. Stall current is not yet known. Phase 4 measures it. |
| N20 6 V 150 RPM | Runs from one cell at lower speed than the 6 V rating. Published stall current is about 0.25 A, which the DRV8833 can carry. |
| GP2S700HCP | LED forward voltage about 1.2 V typical at 20 mA. With 470 Ω from 3.3 V and about 0.4 V across the PCF8574 pin, each LED runs at 3.5–4.5 mA, near the datasheet’s 4 mA test current. Output is analog, so no I2C address and no multiplexer. |
| MAX98357A | I2S, no master clock. VIN from the switched cell. SD needs above 1.4 V for the left channel; the safe switch gives about 2.7 V against the internal 100 kΩ pulldown. Speaker wires go only to OUT+ and OUT−, never to ground. |
| Microphone | GPIO42 clock and GPIO41 data, on the Sense board. Half-duplex: the mic is muted while the speaker plays. |
| Camera | Still JPEG only, sent to the laptop. Bob does not run a local LLM or a desktop OCR stack. |
| Wi-Fi | 2.4 GHz. Fit the included antenna, away from the copper pad. |

## Power

```
Protected 18650
   + ---- [ POWER SWITCH ] ----+---- XIAO BAT+
                               +---- DRV8833 VM ---- C1 1000 µF + C2 100 nF to GND
                               +---- MAX98357 VIN -- C5 100 µF  + C6 100 nF to GND
                               +---- R1 100k ---- midpoint ---- R2 100k ---- GND
                                                     |
                                                     +---- C9 100 nF to GND
                                                     +---- ADS1115 AIN3
   - ---------------------------------------- all grounds, including XIAO BAT-

XIAO 3V3 pin ---- C7 10 µF + C8 100 nF to GND
```

![Bob full wiring](images/bob-wiring.png)

![Bob circuit details](images/bob-circuit-details.png)

One sheet per part, showing the XIAO pins and every extra resistor and capacitor, is in `images/parts/` and embedded in `Bob-pins.md`. Redraw all of them with `.venv\Scripts\python tools\draw_circuit.py`.

If Bob shuts off the moment the power switch closes, the cell protection is tripping on the capacitor inrush. Plug in USB to reset it, then fit 470 µF in place of C1.

Seeed’s wiring note: the battery negative pad is the one closer to the USB connector. Positive is the pad farther from USB. Check with a meter before soldering.

The switch is in the battery positive lead. USB programming works with the switch off. Charging through the XIAO requires the switch on, because that is what connects the cell.

Rules:

- One charger only: the circuit on the XIAO.
- The protected cell provides overcharge, over-discharge, and overcurrent protection. The XIAO charger does not replace that protection board. A plain holder does not provide it either.
- Motors take current from the cell through the DRV8833, not from the 3.3 V pin. Seeed allows about 700 mA from 3.3 V; the OLED, ADC, expander, and sensor LEDs stay on that rail.
- 100 kΩ pulldown on every DRV8833 input so a reset cannot start a motor.
- 100 nF ceramic across each motor's tabs, to keep brush noise off the ADC and Wi-Fi.
- Every pull-up and sensor collector uses the XIAO 3V3 pin. Nothing on 3V3 goes to the DRV8833.
- Motion stays locked after boot until a 2-second touch. Charge the robot on the bench. Unplug USB before Bob is allowed to drive.
- Software warning around 3.5 V at the cell. Motor lock around 3.4 V. Confirm both with a meter in Phase 3. Below the lock threshold Bob can still show the warning, then sleep.
- Divider math: midpoint voltage is half the cell. 4.2 V becomes 2.1 V at the ADC. Bleed current is about 21 µA.

### Runtime, as a planning estimate

Usable capacity is assumed to be 80% of 2500 mAh, so 2000 mAh. Seeed’s published Sense figures used below are Wi-Fi active about 110 mA, and deep sleep about 3 mA. The other lines are allowances, not measurements.

| State | Allowance | Where it comes from |
| --- | --- | --- |
| Awake, Wi-Fi on, camera off, motors off | 110 mA | Seeed Sense Wi-Fi active figure |
| OLED | 15 mA | Allowance |
| Three IR LEDs | 14 mA | About 4.5 mA each |
| ADC, expander, idle electronics | 5 mA | Allowance |
| **Awake idle total** | **about 145 mA** | Sum of the rows above |
| Speaking, mic or amp active | 220 mA | Planning allowance |
| Moving | 350 mA | Planning allowance on top of the idle electronics |

A mix of 70% idle, 20% talking, and 10% moving is about 180 mA. At 2000 mAh that is on the order of 10 hours. Treat that as a budget, then replace it with the Phase 3 measurement.

Sleep, if the Sense board really draws about 3 mA and the LEDs and amplifier are off, is on the order of two weeks from 2000 mAh. The two safe switches add about 0.35 mA and the battery divider about 0.02 mA, so plan on about 3.4 mA. If the camera will not standby, sleep may only last a day or two. Phase 7 is the number that counts.

## Pins

D11 and D12 stay with the microphone. The camera connector is left untouched.

| XIAO pin | GPIO | Function |
| --- | --- | --- |
| D0 | GPIO1, touch 1 | Copper pad through R13 470 Ω. Deep-sleep wake. |
| D1 | GPIO2 | Both bumper switches in parallel. R14 10 kΩ pull-up, C14 100 nF to GND. Pressed = low. |
| D2 | GPIO3 | DRV8833 AIN1, PWM. R3 100 kΩ to GND. |
| D3 | GPIO4 | DRV8833 AIN2, PWM. R4 100 kΩ to GND. |
| D4 | GPIO5 | I2C SDA. OLED, ADS1115, PCF8574. |
| D5 | GPIO6 | I2C SCL |
| D6 | GPIO43 | I2S BCLK to the MAX98357A. Also prints the boot log. |
| D7 | GPIO44 | I2S LRCLK |
| D8 | GPIO7 | DRV8833 BIN1, PWM. R5 100 kΩ to GND. J3 cut. |
| D9 | GPIO8 | DRV8833 BIN2, PWM. R6 100 kΩ to GND. J3 cut. |
| D10 | GPIO9 | I2S DIN |
| D11 | GPIO42 | PDM microphone clock. Do not move. |
| D12 | GPIO41 | PDM microphone data. Do not move. |

### I2C devices

| Device | Address | Role |
| --- | --- | --- |
| SSD1306 OLED | 0x3C | Status |
| ADS1115 | 0x48 | Three edge sensors and the battery divider |
| PCF8574 | 0x20 | Enables and the driver fault input |

Check the bus pull-ups with power off: SDA and SCL to 3V3 should read 1.5–10 kΩ. Above 10 kΩ, fit R23 / R24 (4.7 kΩ). Below 1.5 kΩ, remove the pull-ups from one module.

ADS1115 channels, single-ended, ±4.096 V range:

| Channel | Signal | Filter |
| --- | --- | --- |
| AIN0 | Front-left GP2S emitter | C10 100 nF |
| AIN1 | Front-right GP2S emitter | C11 100 nF |
| AIN2 | Front-center GP2S emitter | C12 100 nF |
| AIN3 | Battery divider midpoint. Cell voltage = 2 × reading. | C9 100 nF |

### Safe switches on the PCF8574

The expander powers up with its pins released (weak high). Every output is wired so that “released” means off.

P0 sinks the three sensor LED cathodes directly. Released, no current flows and the LEDs are off.

P1 and P2 each drive one BC547 safe switch:

- R15 / R18 100 kΩ from the PCF pin to 3.3 V.
- R16 / R19 100 kΩ from that pin to the base of Q1 / Q2. Emitter to ground.
- The collector is the enable line.
- R17 / R20 22 kΩ from the enable line to 3.3 V.

Released, the base is pulled up, the BC547 conducts and holds the enable line low. Firmware writes 0, the BC547 turns off and the 22 kΩ lifts the enable line to about 2.7 V (amp SD) or 3.2 V (driver nSLEEP). Each switch draws about 0.17 mA while released.

| PCF pin | Wired to | Released (boot, reset, sleep) | Firmware writes 0 |
| --- | --- | --- | --- |
| P0 | Three sensor LED cathodes (LED_K) | LEDs off | LEDs on |
| P1 | Q1 → MAX98357A SD_MODE | Amplifier off | Amplifier on, left channel |
| P2 | Q2 → DRV8833 nSLEEP | Driver asleep | Driver awake |
| P3 | DRV8833 nFAULT, R21 10 kΩ to 3.3 V | Input: 1 = OK, 0 = fault | Never write 0 |
| P4–P7 | Spare | Leave released | — |

The PCF8574 keeps its outputs through an XIAO reset. The first line of `setup()` writes 0xFF; write 0xFF again before deep sleep. Motor inputs still have their own 100 kΩ pulldowns. A low P3 stops both motors and ends the patrol.

BC547 pinout, flat face toward you, legs down: collector, base, emitter.

For the early bench tests, before this block is built, you may tie nSLEEP and the amplifier SD pin high only while the wheels are in the air and you are watching them. The finished robot uses the transistor switches.

### Edge-sensor circuit, repeated three times

- LED anode toward 3.3 V through 470 Ω (R7 / R8 / R9). Cathode to the shared LED_K line, which goes to PCF8574 P0.
- Phototransistor collector to 3.3 V. Emitter through 10 kΩ (R10 / R11 / R12) to ground, and 100 nF (C10 / C11 / C12) to ground. Emitter node to the ADS1115 channel.
- One 100 nF (C13) from 3.3 V to ground on the sensor lip.

Read each sensor twice, LEDs off then LEDs on, and use the difference; that cancels room light. Wait 5 ms after each LED change, because 10 kΩ × 100 nF is a 1 ms filter.

No object: the ADC reading sits near 0 V. A surface about 3 mm away raises the voltage. The exact “table present” number is measured on Bob’s own desk in Phase 6. A disconnected sensor, a stuck full-scale reading, or an I2C failure means stop.

### Motor truth table

Speed is a PWM duty. The cap for version 1 is 40% until Phase 5 measures real wheel speed. One command may run for at most 400 ms.

| Command | Left motor | Right motor | Extra rule |
| --- | --- | --- | --- |
| Stop | Coast, then inputs low | Coast, then inputs low | Always available |
| Forward | Forward | Forward | All three sensors must see the table |
| Pivot left | Stop | Short forward | Center and left sensors must see the table. 250 ms cap |
| Pivot right | Short forward | Stop | Center and right sensors must see the table. 250 ms cap |
| Reverse | — | — | Disabled until a rear sensor exists |

The laptop may ask for a move. It cannot toggle a motor pin. Firmware accepts a move only when every check below is true.

```
allow move only when
  motion has been unlocked by a 2-second touch
  battery is above the lock threshold
  ADS1115 and all three sensors answer
  each sensor is inside its calibrated "table" window
  bumper is released
  DRV8833 fault line (PCF P3) is high
  direction is forward, pivot-left, or pivot-right
  duty is at most 40 percent
  duration is at most 400 ms, or 250 ms for a pivot
  the previous move has already stopped
```

If a sensor fails during the move, both motors stop immediately. A bumper press stops immediately. There is no automatic reverse.

### MAX98357A

| Amp pin | Connect to |
| --- | --- |
| VIN | Switched battery, C5 100 µF + C6 100 nF to GND |
| GND | Common ground |
| BCLK | D6 |
| LRC | D7 |
| DIN | D10 |
| SD | Q1 safe switch (PCF P1) |
| GAIN | R22 100 kΩ to VIN, 3 dB |
| OUT+ / OUT− | Speaker, either way around |

Audio is 16-bit, mono, 16 kHz, I2S, left slot. The microphone is stopped before playback starts.

## Layout

Bottom layer, as low as possible: 18650 on its side, switch at the rear, skid behind the wheels.

Middle: two motors on the left and right, DRV8833, the large capacitor next to the driver.

Top: XIAO with the camera looking slightly downward, OLED on the front face, speaker above the battery and away from the microphone hole. Do not cover the mic opening or the antenna with copper foil.

Front lip, ahead of the wheel contact by at least 25 mm: left, center, and right GP2S700HCP, facing the table, about 3 mm clear, with a small shroud. At 40 mm/s, 150 ms of stopping distance is only 6 mm, but the sensor sees the surface under itself, so the lip has to reach the edge before the wheel does.

Make a cardboard body in Phase 12 and write the real width, depth, and height on it. Do not print a case first.

## Software

The code is in [`code/`](code/README.md): one test sketch per part in `code/tests/` (T01–T13, each with its own instructions and wiring image), the complete firmware in `code/bob/`, and the laptop server in `code/laptop/`. The phases below say which test to run.

Firmware and the laptop stay apart.

**On Bob:** camera stills, PDM microphone, I2S speaker, OLED, touch and wake, sleep, battery reading, motor driver, parked encoder connectors, edge sensors, bumper, Wi-Fi, and the motion gate.

**On the laptop, Python and FastAPI:** WebSocket session, speech-to-text, the “Hey Bob” phrase check, the language model, vision and OCR, text-to-speech, and a small database for reminders, events, interviews, and learning plans.

Suggested WebSocket messages:

```json
{ "type": "audio", "pcm_b64": "..." }
{ "type": "image", "jpeg_b64": "..." }
{ "type": "status", "state": "idle", "battery_v": 3.9 }

{ "type": "listen", "active": true }
{ "type": "show", "line1": "Listening", "line2": "" }
{ "type": "say", "text": "Interview tomorrow at 10.", "pcm_b64": "..." }
{ "type": "move", "dir": "forward", "duty": 30, "ms": 300 }
```

The laptop’s move request is a suggestion. The gate in the previous section is the decision.

States: `asleep`, `awake`, `listening`, `thinking`, `speaking`, `moving`.

“Hey Bob” is handled only in `awake`. The server transcribes short microphone chunks. A transcript that starts with “hey bob” returns `listen.active = true`. The following utterance is the command. “Stop listening”, a finished reply, or the inactivity timer leaves listening mode.

If Wi-Fi is down, the OLED shows `Offline`. Motors refuse remote move requests. Touch and sleep still work. Reminders are not guessed locally.

Privacy: the camera takes a still only after a request such as “read this note”. The microphone runs only while Bob is awake, and pauses while the speaker plays. The laptop keeps reminder text and discards the raw image and audio after the reply, unless you later turn storage on.

The XIAO needs the Arduino board `XIAO_ESP32S3`, PSRAM set to OPI, and USB CDC. Camera code starts from Seeed’s Sense example after the camera marking is known. Microphone code starts from Seeed’s PDM example.

Pins and the first lines of `setup()`:

```cpp
#include <Wire.h>

constexpr int PIN_TOUCH = D0, PIN_BUMPER = D1;
constexpr int PIN_AIN1 = D2, PIN_AIN2 = D3, PIN_BIN1 = D8, PIN_BIN2 = D9;
constexpr int PIN_I2S_BCLK = D6, PIN_I2S_LRC = D7, PIN_I2S_DIN = D10;
constexpr uint8_t PCF_ADDR = 0x20;  // 0x38 on a PCF8574A
constexpr uint8_t PCF_LEDS = 1 << 0, PCF_AMP = 1 << 1, PCF_DRIVER = 1 << 2, PCF_FAULT = 1 << 3;

uint8_t pcfOut = 0xFF;  // every pin released: LEDs, amp and driver off, P3 readable

void pcfWrite(uint8_t value) {
  pcfOut = value | PCF_FAULT;  // P3 must stay released to read nFAULT
  Wire.beginTransmission(PCF_ADDR);
  Wire.write(pcfOut);
  Wire.endTransmission();
}

void setup() {
  Wire.begin();
  pcfWrite(0xFF);  // the PCF8574 kept its state through the reset
  for (int p : {PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2}) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }
  pinMode(PIN_BUMPER, INPUT);  // R14 is the pull-up
  // ...
}
```

Write a PCF bit as 0 to turn that part on, for example `pcfWrite(pcfOut & ~PCF_DRIVER)`. Call `pcfWrite(0xFF)` before `esp_deep_sleep_start()`.

Bring-up motion lock:

```cpp
bool motionUnlocked = false;

bool moveAllowed(int duty, int ms, const char *dir) {
  if (!motionUnlocked) return false;
  if (!batteryOk || !sensorsOk || bumperPressed || driverFault) return false;
  if (duty < 0 || duty > 40) return false;
  if (strcmp(dir, "forward") == 0)
    return ms > 0 && ms <= 400 && tableUnderLeft && tableUnderRight && tableUnderCenter;
  if (strcmp(dir, "pivot_left") == 0) return ms > 0 && ms <= 250 && tableUnderCenter && tableUnderLeft;
  if (strcmp(dir, "pivot_right") == 0) return ms > 0 && ms <= 250 && tableUnderCenter && tableUnderRight;
  return false;  // reverse and unknown commands are refused
}
```

Phrase check on the laptop:

```python
def heard_hey_bob(transcript: str) -> bool:
    words = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in transcript)
    return words.strip().startswith("hey bob")
```

Reminders are rows in SQLite: title, due time, kind (`task`, `event`, `interview`, `learning`), and a short note. The laptop scheduler pushes a due item the next time Bob is awake and connected. Bob speaks one item and shows it on the OLED. He does not drive anywhere because a reminder fired.

## Build phases

Stop at the first failed pass. Do not skip to the table.

### Phase 1 — Board, camera, microphone

**Code.** [`T01_camera`](code/tests/T01_camera/README.md), [`T02_microphone`](code/tests/T02_microphone/README.md).

**Wire.** XIAO, antenna, USB-C. Solder C7 10 µF and C8 100 nF from 3V3 to GND at the pin. Cut J3 on the Sense board. Nothing else.

**Test.** With power off, D8 and D9 must not read a few kΩ to 3V3 (J3 is cut). Confirm the board as `XIAO_ESP32S3` with OPI PSRAM. Run Seeed’s camera example and microphone example. Read the text on the camera module and write down OV2640 or OV3660.

**Pass.** A Wi-Fi still image appears, and the serial plot shows the microphone responding to a clap.

**If it fails.** Charge-only USB cable, antenna not seated, or PSRAM left disabled. Do not cut the mic jumpers to “free” D11 and D12.

### Phase 2 — OLED and touch

**Code.** [`T03_i2c_scan`](code/tests/T03_i2c_scan/README.md), [`T04_oled`](code/tests/T04_oled/README.md), [`T05_touch`](code/tests/T05_touch/README.md).

**Wire.** OLED VCC to 3.3 V, GND, SCL to D5, SDA to D4. One copper pad to D0 through R13 470 Ω, soldered within a few mm of the pin, then a short wire. The pad must not touch ground or the antenna.

**Test.** I2C scan shows 0x3C. The screen prints `Bob`. Read the touch channel on GPIO1 while touching and releasing the pad. Record both numbers.

**Pass.** The two touch readings are far apart and stable.

**If it fails.** Wrong I2C address (try 0x3D), missing pull-ups, or the pad wire is too long. If the channel never moves, plan a TTP223 on D0 later. Do not buy it until this test is repeated on the finished body.

### Phase 3 — Battery and rails

**Code.** [`T06_battery_adc`](code/tests/T06_battery_adc/README.md).

**Wire.** Protected cell, holder, switch, XIAO battery pads with the polarity in Seeed’s note. Meter the switched battery before it touches the board. Add the divider (R1, R2, C9) on a breadboard and read it with the ADS1115 on A3. Cell voltage is 2 × the reading.

**Test.** Switch off: USB still programs the board. Switch on, USB plugged: the red charge LED behaves as Seeed describes (flashing while charging, off when full). Measure charge current. Compare the divider reading with the meter from 4.2 V down toward 3.4 V.

**Pass.** Polarity is correct, only one charger is connected, and the ADC matches the meter within about 50 mV.

**If it fails.** Stop and remove power. A reversed cell or a second charger is not a software problem.

### Phase 4 — Motors, wheels in the air

**Code.** [`T07_pcf8574`](code/tests/T07_pcf8574/README.md) (safe switches first), then [`T08_motors`](code/tests/T08_motors/README.md).

**Wire.** DRV8833 VM to the switched cell with C1 1000 µF and C2 100 nF beside it. No 3.3 V wire: the module has no logic supply pin. Grounds common. AIN1 / AIN2 to D2 / D3 and BIN1 / BIN2 to D8 / D9, each with its 100 kΩ pulldown (R3–R6). Outputs to the two motors, with C3 / C4 100 nF across each motor's tabs. FLT to R21 10 kΩ to 3.3 V (and to PCF P3 once the expander is fitted). Encoder plugs are taped back. Wheels off, or the body held so nothing can touch the table.

**Test.** Stall each motor for one second into an ammeter, or measure supply current while holding the shaft. Then run 30% duty forward and back for each motor.

**Pass.** Each motor turns the commanded way, current stays under 0.4 A at stall, FLT stays high, and nothing moves when you press reset in the middle of a run.

**If it fails.** Swap that motor’s two leads to fix direction. If stall current is high or the N12 will not turn, switch to the N20 6 V 150 RPM fallback and repeat this phase.

### Phase 5 — Slow motion on the floor

**Code.** [`T08_motors`](code/tests/T08_motors/README.md) with `+` / `-` to find the duty, then set `DUTY_CAP_PERCENT` in `code/bob/config.h`.

**Wire.** Fit wheels only after the shaft matches. Still no table.

**Test.** On the floor, 30% duty, 300 ms forward. Measure how far Bob travels. Lower the duty until a 300 ms move is about one centimetre to a few centimetres. Mark the duty that produces about 30–40 mm/s and make that the software cap, still never above 40% until you choose to raise it.

**Pass.** Ten repeats travel a similar distance, and stop is immediate when the command ends.

**If it fails.** One motor is reversed, a wheel is slipping, or the battery sags enough to reset the XIAO. Check that C1 sits right at the driver's VM pin and that C3 / C4 are on the motor tabs, then repeat. Encoders stay unwired.

### Phase 6 — Edge sensors and bumper

**Code.** [`T09_edge_sensors`](code/tests/T09_edge_sensors/README.md), [`T10_bumper`](code/tests/T10_bumper/README.md).

**Wire.** Build the three GP2S channels (R7–R12, C10–C13) and the bumper (R14 10 kΩ pull-up, C14 100 nF). Join the three LED cathodes to PCF P0. Mount the sensors on a stick at about 3 mm above a sample of the real desk, 25 mm ahead of where the wheels will be.

**Test.** Log all three voltages on the desk, over white paper, over black material, and over the real edge with a hand holding the body. Choose a window that is true on the desk and false over the edge. Unplug one sensor. Hold the bumper.

**Pass.** Desk readings sit inside the window, the edge sits outside it, an unplugged sensor forbids motion, and the bumper reads low when pressed.

**If it fails.** Change the 10 kΩ emitter resistor, the height, or the shroud. A black desk that looks like an edge means Bob will refuse to drive there. Use a lighter sheet, or stop and reconsider the sensor. Do not widen the window until a real edge also passes.

### Phase 7 — Sleep and touch wake

**Code.** [`T12_sleep_wake`](code/tests/T12_sleep_wake/README.md).

**Wire.** Safe-switch block installed: Q1 and Q2 with R15–R20. IR LEDs, amplifier, and motor driver must be off when their PCF pins are released. Firmware writes 0xFF to the PCF8574 before sleeping.

**Test.** Set the inactivity timer to 20 seconds. Confirm motors are stopped, the screen is off, and the LED current is gone. Measure battery current. Touch the pad. Bob boots, reconnects, and prints a greeting. Saying “Hey Bob” while he is asleep must not wake him.

**Pass.** Wake is reliable from a deliberate touch, and sleep current is understood. Write the measured milliamps into this file.

**If it fails.** Recalibrate the touch threshold on the finished pad. If the pad false-wakes, move to a TTP223 on D0 and GPIO wake. If sleep current stays high, the camera is the first suspect.

### Phase 8 — Speaker

**Code.** [`T11_speaker`](code/tests/T11_speaker/README.md).

**Wire.** MAX98357A as in the audio table: BCLK D6, LRC D7, DIN D10, C5 + C6 on VIN, R22 100 kΩ from GAIN to VIN.

**Test.** Play a short local tone with the microphone muted. Then play a short clip while watching supply current.

**Pass.** The tone is clear at a desk volume and the speaker stays cool.

**If it fails.** A silent amp is often SD_MODE held low (P1 not written 0, or Q1 wired backwards), or speaker wires tied to ground by mistake. A click at every reset is the boot log on D6 while the amp is still on: make sure P1 is released before any reset.

### Phase 9 — Laptop brain and “Hey Bob”

**Code.** [`code/laptop`](code/laptop/README.md) server, [`T13_wifi_link`](code/tests/T13_wifi_link/README.md), then the complete firmware [`code/bob`](code/bob/README.md).

**Wire.** Bob and the laptop on the same 2.4 GHz network.

**Test.** FastAPI WebSocket receives status. Wake Bob with a touch. Say “Hey Bob, what time is it?” The OLED shows `Listening`, then the spoken answer. Try the same phrase before the touch, while he is asleep.

**Pass.** The command works only when he is awake. A lost network shows `Offline` and does not move the wheels.

**If it fails.** Half-duplex is required: mute the mic while the speaker plays, or Bob will hear himself.

### Phase 10 — Notes and screens

**Test.** In good light, ask Bob to read a large-print sticky note, then a laptop screen. One still, VGA or smaller JPEG. The laptop does OCR or a vision-language pass and returns a short sentence plus any date or task it actually read.

**Pass.** Large print at a few centimetres is usable. Failures are reported as “I could not read that”, not as invented tasks.

**Limits.** Fixed focus, small sensor, glare, and network delay. The XIAO is the camera, not the reader.

### Phase 11 — Reminders and study plans

**Test.** Create an interview, a learning block, and a short task on the laptop. While Bob is awake, he speaks one due item and shows it. Unplug Wi-Fi and confirm he does not invent the next item.

**Pass.** Items survive a laptop restart, and a reminder never starts a motor.

### Phase 12 — Body and supervised driving

**Code.** The complete firmware [`code/bob`](code/bob/README.md); its README has the same checklist with the laptop commands to use.

**Build.** Cardboard mock-up first. Record width, depth, and height. Only then print a case. Battery low, camera and screen high, sensors on the front lip, skid at the rear, antenna and microphone uncovered.

**Table checklist, in order.** All must pass with a hand ready.

1. Wheels in the air: forward and both pivots run, reverse is refused.
2. On the floor, away from any drop: the speed cap from Phase 5 still feels slow.
3. On a board laid on the floor, with foam beyond the edge: Bob stops while the wheels are still on the board.
4. Tape over one sensor: he will not start.
5. Unplug one sensor: he will not start.
6. Bumper tap while moving: stop, no reverse.
7. Battery at the lock threshold: motors refuse, warning shows.
8. A slow supervised approach to a real table edge, with a tether or a hand on the body.
9. Only after 1–8: short supervised moves on the real table. No unattended driving.

Any failed row goes back to Phase 6. Three front sensors plus a bumper are a conservative aid, not a promise that Bob cannot fall.

## Work order

1. Buy the XIAO and finish Phase 1, including the camera marking.
2. OLED and touch.
3. Protected cell and measured charge current.
4. Motors in the air. Keep or replace the N12 based on stall current.
5. Slow floor moves. Set the duty cap.
6. Calibrate the three GP2S700HCP sensors on the real desk.
7. Measure sleep, and prove that only touch wakes Bob.
8. Speaker.
9. “Hey Bob” on the laptop, using the built-in microphone, only while awake.
10. Sticky notes and screen stills.
11. Reminders.
12. Cardboard body, then the supervised checklist.

The first purchase is the XIAO, a data cable, and a multimeter if you do not have one. Everything else waits until the matching phase starts.
