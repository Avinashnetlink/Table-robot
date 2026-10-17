# Robot components — use, purpose and checklist

This is the component list for the **three downward-facing VL53L0X** version of Bob. Each row explains the part's job and why it is included in this circuit. Quantities are for one robot; the Have / Order / Tested boxes remain your build checklist.

[Full circuit and connections](CIRCUIT.md) · [Individual component circuits and tests](../code/tests/README.md) · [Complete robot testing](TESTING.md)

The XIAO reads sensors and controls the robot locally. The laptop handles the server, commands, reminders and optional speech/image processing. The downward sensors check for a supported tabletop; the bumpers detect contact with obstacles. The camera is for photos, not a validated cliff or obstacle detector.

Inventory status is **unknown**. No item has been marked owned or tested. Check **Have** after identifying the exact part, **Order** only if it is missing or unsuitable, and **Tested** after the corresponding bench check. Do not reorder parts simply because these boxes are empty. Record substitutions before wiring.

## Main assembly

| Item | Qty needed | Use in Bob / why it is included | Have | Order | Tested | What to check / test |
| --- | ---: | --- | :---: | :---: | :---: | --- |
| Seeed XIAO ESP32-S3 **Sense** | 1 | Main controller: reads sensors, runs local motion safety and drives motor/audio commands. Chosen as the project platform because it combines ESP32-S3 processing, Wi-Fi and the Sense camera/microphone connections. | [ ] | [ ] | [ ] | Sense, not Plus; camera and PDM expansion included; record board revision; [T01](../code/tests/T01_camera/README.md)/[T02](../code/tests/T02_microphone/README.md) |
| Camera on the Sense assembly | 1, included | Captures photos for viewing and optional laptop OCR. Uses the fitted camera connector; it is not used as the motor safety sensor. | [ ] | [ ] | [ ] | Record the fitted camera model; [T01](../code/tests/T01_camera/README.md). Do not order another camera if the kit already includes it. |
| PDM microphone on the Sense assembly | 1, included | Captures sound for optional laptop speech recognition and commands. Uses the built-in mic so a separate microphone module is unnecessary; voice does not wake deep sleep. | [ ] | [ ] | [ ] | Keep microphone jumpers intact; [T02](../code/tests/T02_microphone/README.md). Included on the Sense expansion board. |
| 2.4 GHz antenna + fitted connector | 1 | Provides the radio connection to the laptop. Needed for reliable Wi-Fi command, audio, image and status transfer. | [ ] | [ ] | [ ] | Fully seated, away from metal and touch foil; [T13](../code/tests/T13_wifi_link/README.md) |
| USB-C **data** cable | 1 | Uploads firmware, supplies bench power and carries Serial diagnostics. A charge-only cable cannot upload code or show readings. | [ ] | [ ] | [ ] | Board enumerates, not charge-only |
| SSD1306 OLED, 128×64, 4-pin I²C | 1 | Shows eyes, text and status on the robot. I²C lets it share two signal wires with the other bus devices. | [ ] | [ ] | [ ] | 3.3 V compatible; not SH1106; address 0x3C; [T03](../code/tests/T03_i2c_scan/README.md)/[T04](../code/tests/T04_oled/README.md) |
| Copper touch pad, about 20×30 mm | 1 | Provides local touch input for interaction, deliberate motion arming and wake from sleep. Gives the user a physical input on the robot. | [ ] | [ ] | [ ] | Isolated, short lead, not over antenna; [T05](../code/tests/T05_touch/README.md)/[T12](../code/tests/T12_sleep_wake/README.md) |
| Protected 1S rechargeable 18650, nominal 3.6/3.7 V | 1 | Stores energy for untethered use. The selected circuit uses one cell for XIAO battery power, motor supply and audio; cell protection complements the fuse and software checks. | [ ] | [ ] | [ ] | 4.2 V charge chemistry; reputable cell; continuous current meets measured load; [T06](../code/tests/T06_battery_adc/README.md) |
| Single-cell holder with secure contacts | 1 | Holds the battery and carries power into the circuit. Secure, insulated contacts prevent intermittent power and accidental shorts. | [ ] | [ ] | [ ] | Fits protected cell length, correct polarity, retention and insulation |
| Main DC switch SW1 | 1 | Switches the battery feed to the robot. Useful for normal battery-powered on/off; USB can still power the XIAO, so this is not complete isolation with USB attached. | [ ] | [ ] | [ ] | DC rating exceeds measured load/inrush; choose a robust 5 A class part |
| Inline fuse holder + suitable fuse F1 | 1 set | Interrupts excessive battery current during a fault. Protects the supply wiring when its rating is chosen for the measured load and wiring limits. | [ ] | [ ] | [ ] | Rating after current tests, below wire/switch/cell limits |
| Accessible motor-power kill switch SW2 | 1 | Physically disconnects the motor VM supply. Lets the user remove motor power even while USB keeps the controller running. | [ ] | [ ] | [ ] | Opens motor VM branch even with USB attached |
| N12 5 V ~57 RPM gearmotor | 2 | Turns a drive wheel through reduction gears. Two independently driven motors allow forward motion and differential steering; usable torque/current on the 1S supply must be measured. | [ ] | [ ] | [ ] | Record exact model, shaft and current; encoder wires unused; [T08](../code/tests/T08_motors/README.md) |
| 34 mm wheels matching actual shaft | 2 | Transfer motor rotation to the tabletop. Matching the shaft avoids slipping; wheel size and grip affect speed and stopping distance. | [ ] | [ ] | [ ] | Buy after measuring shaft; 3 mm D-shaft only if motors match |
| DRV8833 dual driver module | 1 | Switches battery power to both motors under XIAO PWM control. GPIOs cannot supply motor current; this driver also exposes sleep control and fault feedback. | [ ] | [ ] | [ ] | Actual DRV8833; exposes nSLEEP + nFAULT; no hard-tied enable; [T07](../code/tests/T07_pcf8574/README.md)/[T08](../code/tests/T08_motors/README.md) |
| Robu VL53L0X carrier (selected) | 3 | Measures distance down to the desk at left, right and center. Firmware uses the three readings to detect loss of tabletop support and inhibit motion; calibration is essential. | [ ] | [ ] | [ ] | Downward left/right/center; three matching boards; 3.3 V VIN/host compatibility; [T09](../code/tests/T09_edge_sensors/README.md) |
| TCA9548A carrier | 1 | Selects one of the three sensor I²C branches. Needed in this design because all three VL53L0X sensors use address 0x29; separate branches avoid address collisions without extra XSHUT GPIOs. | [ ] | [ ] | [ ] | Required: channels 0/1/2, address 0x70; RESET pull-up; [T03](../code/tests/T03_i2c_scan/README.md)/[T09](../code/tests/T09_edge_sensors/README.md) |
| ADS1115 (not ADS1015) | 1 | Measures the battery-divider voltage on A3 over I²C. Retained because the current pin map has no free XIAO analog input; battery readings support low-voltage warnings and motion lockout. | [ ] | [ ] | [ ] | 3.3 V supply, ADDR grounded for 0x48; battery A3 only, unused A0–A2 to GND; [T03](../code/tests/T03_i2c_scan/README.md)/[T06](../code/tests/T06_battery_adc/README.md) |
| PCF8574 / PCF8574A breakout | 1 | Adds control/input lines over the shared I²C bus. P1/P2 control amplifier and motor enables through Q1/Q2; P3 reads driver faults, preserving XIAO pins for PWM and audio. | [ ] | [ ] | [ ] | 3.3 V, address 0x20 / 0x38, three address straps grounded; [T03](../code/tests/T03_i2c_scan/README.md)/[T07](../code/tests/T07_pcf8574/README.md) |
| MAX98357A amplifier breakout | 1 | Converts the XIAO digital I²S audio stream into speaker power. Needed because the GPIO audio signals cannot directly drive the speaker. | [ ] | [ ] | [ ] | A = I²S; B uses a different data format; SD exposed, removable board pull-ups; [T11](../code/tests/T11_speaker/README.md) |
| Speaker, 4 Ω | 1 | Converts the amplified signal into audible speech, reminders and tones. Completes the robot’s sound output path. | [ ] | [ ] | [ ] | 3 W recommended if ordering; existing ~1 W requires measured power limit; [T11](../code/tests/T11_speaker/README.md) |
| Bumper microswitch with COM/NO/NC | 2 | Reports physical obstacle contact at either front bumper. Provides a contact-stop input; it does not detect obstacles before impact or replace the downward sensors. | [ ] | [ ] | [ ] | Both operate separately; choose NO parallel or optional NC series wiring; [T10](../code/tests/T10_bumper/README.md) |
| Rear skid / caster | 1 | Supports the chassis behind the two drive wheels while allowing turns. Helps maintain the intended sensor height and robot balance. | [ ] | [ ] | [ ] | Stable support, no cable snag |
| BC547 NPN, Q1/Q2 | 2 + 1 spare | Invert the PCF enable signals for amplifier SD and driver nSLEEP. With the associated resistors, released PCF outputs command the loads off; this is not an independent watchdog. | [ ] | [ ] | [ ] | Confirm actual manufacturer pinout; do not assume another NPN matches |

## Passive parts and construction

Used counts match the base circuit; ordering small packs is convenient. These are minimum fitted counts, not pack sizes.

| Item | Qty used | Have | Order | Tested | References / purpose |
| --- | ---: | :---: | :---: | :---: | --- |
| 100 kΩ resistors | 11 | [ ] | [ ] | [ ] | R1/R2 halve VBAT for ADC measurement; R3–R6 hold motor inputs low when GPIOs are undriven; R15/R18 bias the enable inverter inputs; R16/R19 limit transistor base current; R22 selects amplifier gain. [T06](../code/tests/T06_battery_adc/README.md)/[T07](../code/tests/T07_pcf8574/README.md)/[T08](../code/tests/T08_motors/README.md)/[T11](../code/tests/T11_speaker/README.md). |
| 22 kΩ resistors | 2 | [ ] | [ ] | [ ] | R17/R20 pull amplifier SD / driver nSLEEP high when Q1/Q2 are off, completing the enable circuits. [T07](../code/tests/T07_pcf8574/README.md)/[T08](../code/tests/T08_motors/README.md)/[T11](../code/tests/T11_speaker/README.md). |
| 10 kΩ resistors | 2 + up to 4 if missing on carriers | [ ] | [ ] | [ ] | R14 gives an idle HIGH on the bumper input; R21 gives an inactive HIGH on nFAULT. Optional R25 keeps mux RESET inactive; optional R32–R34 keep sensors out of shutdown. Add only missing carrier pull-ups to the correct rails. [T03](../code/tests/T03_i2c_scan/README.md)/[T07](../code/tests/T07_pcf8574/README.md)/[T09](../code/tests/T09_edge_sensors/README.md)/[T10](../code/tests/T10_bumper/README.md). |
| 470 Ω resistors | 1 | [ ] | [ ] | [ ] | R13 is in series with the touch pad, limiting fast transient current into the touch input. Keep it near D0; it is not complete ESD protection. [T05](../code/tests/T05_touch/README.md)/[T12](../code/tests/T12_sleep_wake/README.md). |
| 4.7 kΩ resistors | As measured on upstream + 3 branches | [ ] | [ ] | [ ] | R23/R24 pull upstream SDA/SCL high; R26–R31 do the same on sensor branches. I²C needs pull-ups to communicate; existing carrier resistors may already provide them. Inspect resistance and the correct rail before adding. [T03](../code/tests/T03_i2c_scan/README.md). |
| 100 nF ceramic capacitors | 7 + missing module decoupling | [ ] | [ ] | [ ] | C2/C6/C8 bypass fast supply noise; C3/C4 reduce motor-terminal switching noise; C9 filters battery ADC readings; C14 filters bumper contact noise. Add local IC decoupling only where a breakout lacks it. [T06](../code/tests/T06_battery_adc/README.md)/[T08](../code/tests/T08_motors/README.md)/[T10](../code/tests/T10_bumper/README.md)/[T11](../code/tests/T11_speaker/README.md) and full-robot checks. |
| 1000 µF electrolytic, ≥10 V | 1 | [ ] | [ ] | [ ] | C1 at driver VM supplies brief current transients and reduces motor-rail dips. Observe polarity and measure inrush; it cannot compensate for an undersized supply. [T08](../code/tests/T08_motors/README.md). |
| 100 µF electrolytic, ≥10 V | 1 | [ ] | [ ] | [ ] | C5 buffers the amplifier supply during audio current peaks, helping reduce supply dips. Observe polarity. [T11](../code/tests/T11_speaker/README.md). |
| 10 µF capacitor | 1 | [ ] | [ ] | [ ] | C7 adds local charge storage on 3V3 for controller/peripheral load changes; C8 handles faster noise. Verify rail sag during full-robot tests. |
| 22–24 AWG flexible power wire | As needed | [ ] | [ ] | [ ] | Carries battery, motor and amplifier current with lower resistance than thin signal wire. Keep runs short and verify current/voltage-drop limits. |
| 26–30 AWG signal wire | As needed | [ ] | [ ] | [ ] | Carries low-current control, I²C and analog signals. Short, organized runs reduce noise pickup and bus problems. |
| Heat-shrink, insulated connectors, strain relief | Set | [ ] | [ ] | [ ] | Insulates exposed conductors and secures cables so movement cannot pull joints apart or create shorts. |
| Perfboard + secure ToF/mux headers | Set | [ ] | [ ] | [ ] | Provides stable electrical and mechanical connections between modules. Secure sensor/mux headers prevent intermittent bus faults. |
| Motor brackets, screws, chassis, sensor shrouds | Set | [ ] | [ ] | [ ] | Holds motors and sensors in fixed positions. Consistent sensor height and a clear optical view are necessary for repeatable edge calibration; trial ~60 mm, then validate lip and stopping margin. |

## Optional improvements — order only if wanted or required by tests

| Item | Qty | Have | Order | Tested | When needed |
| --- | ---: | :---: | :---: | :---: | --- |
| Independent motor watchdog / power gate | Design needed | [ ] | [ ] | [ ] | Would remove motor power if controller execution stalls, addressing a limit of software-only deadlines. Not implemented or included in the base circuit; engineer and verify the design before ordering or relying on unattended motion. |

## Required outside the robot

| Item | Use / why it is needed | Where to set up or test |
| --- | --- | --- |
| Laptop or desktop running the Bob server | Runs the network server, commands and reminders; optional speech recognition, speech generation and OCR run here. The XIAO retains local sensor checks and motor control. No general LLM is configured. | [Laptop setup](../code/laptop/README.md), [T13](../code/tests/T13_wifi_link/README.md); full application tests in [TESTING.md](TESTING.md) |
| Wi-Fi access point / router with a compatible 2.4 GHz network | Connects the robot to the laptop for commands, status, audio and photos. Use the same reachable local network; a stale/missing authenticated heartbeat prevents normal motion arming. | [T13](../code/tests/T13_wifi_link/README.md) |

These are supporting equipment, not additional boards to mount inside Bob.

## Test equipment — borrow or order if missing

| Item | Qty | Have | Order | Tested | Purpose |
| --- | ---: | :---: | :---: | :---: | --- |
| Logic analyzer / oscilloscope | 1 | [ ] | [ ] | [ ] | Shows fast electrical events that a multimeter can miss: PWM, I²C rise time, reset glitches, motor cutoff timing and supply dips. Used on the bench, not installed in the robot. |
| Current-limited bench supply | 1 | [ ] | [ ] | [ ] | Limits current during controlled motor/driver characterization so faults can be investigated without unrestricted battery current. Bench equipment; borrow if missing. |
| Multimeter with fused current input | 1 | [ ] | [ ] | [ ] | Checks polarity, shorts/continuity, supply and enable voltages, battery ADC calibration and current. Bench equipment; current measurements require a fused input in series. |

## Record before enabling motion

| Measurement / identity | Your result | Pass |
| --- | --- | :---: |
| Board + camera revision / camera PID | __________ | [ ] |
| Driver module and exposed SLP/FLT pins | __________ | [ ] |
| Cell model / protected / capacity / current rating | __________ | [ ] |
| Actual charger current, USB present, motor rail disabled | __________ mA | [ ] |
| Left / right startup and controlled stall current | __________ / __________ A | [ ] |
| Peak combined load / minimum 3V3 / minimum VBAT | __________ | [ ] |
| Touch idle / press delta / wake delta | __________ | [ ] |
| Battery ADC error at ~4.2, 3.7, 3.4 V | __________ | [ ] |
| ToF family, channels L/R/C, mounting height, min/max desk bands | __________ | [ ] |
| Surface types and lighting tested | __________ | [ ] |
| Speed / worst measured coast distance / sensor overhang | __________ | [ ] |
| NC series bumper option used? | Yes / No | [ ] |
| Deep sleep current + deliberate wake tested | __________ mA | [ ] |
| All fault-injection tests from TESTING.md complete | Date: __________ | [ ] |

Selected product: [Robu VL53L0X](https://robu.in/product/vl53l0x-tof-based-lidar-laser-distance-sensor/). The circuit requires **three matching modules**. The family is confirmed; quantity owned and bench results are still to be recorded. No GP2S sensors or LED drive components are needed.

Only after the final row passes: set `CALIBRATION_CONFIRMED = true`, rebuild, and perform supervised floor tests before any raised-table test.
