# Have / order / test checklist

Inventory status is **unknown**. No item has been marked owned or tested. Check **Have** after identifying the exact part, **Order** only if it is missing or unsuitable, and **Tested** after the corresponding bench check. Do not reorder parts simply because these boxes are empty. Record substitutions before wiring.

## Main assembly

| Item | Qty needed | Have | Order | Tested | What to check / test |
| --- | ---: | :---: | :---: | :---: | --- |
| Seeed XIAO ESP32-S3 **Sense** | 1 | [ ] | [ ] | [ ] | Sense, not Plus; camera and PDM expansion included; record board revision; T01/T02 |
| 2.4 GHz antenna + fitted connector | 1 | [ ] | [ ] | [ ] | Fully seated, away from metal and touch foil; T13 |
| USB-C **data** cable | 1 | [ ] | [ ] | [ ] | Board enumerates, not charge-only |
| SSD1306 OLED, 128×64, 4-pin I²C | 1 | [ ] | [ ] | [ ] | 3.3 V compatible; not SH1106; address 0x3C; T03/T04 |
| Copper touch pad, about 20×30 mm | 1 | [ ] | [ ] | [ ] | Isolated, short lead, not over antenna; T05/T12 |
| Protected 1S rechargeable 18650, nominal 3.6/3.7 V | 1 | [ ] | [ ] | [ ] | 4.2 V charge chemistry; reputable cell; continuous current meets measured load; T06 |
| Single-cell holder with secure contacts | 1 | [ ] | [ ] | [ ] | Fits protected cell length, correct polarity, retention and insulation |
| Main DC switch SW1 | 1 | [ ] | [ ] | [ ] | DC rating exceeds measured load/inrush; choose a robust 5 A class part |
| Inline fuse holder + suitable fuse F1 | 1 set | [ ] | [ ] | [ ] | New recommendation; rating after current tests, below wire/switch/cell limits |
| Accessible motor-power kill switch SW2 | 1 | [ ] | [ ] | [ ] | New recommendation; opens motor VM branch even with USB attached |
| N12 5 V ~57 RPM gearmotor | 2 | [ ] | [ ] | [ ] | Record exact model, shaft and current; encoder wires unused; T08 |
| 34 mm wheels matching actual shaft | 2 | [ ] | [ ] | [ ] | Buy after measuring shaft; 3 mm D-shaft only if motors match |
| DRV8833 dual driver module | 1 | [ ] | [ ] | [ ] | Actual DRV8833; exposes nSLEEP + nFAULT; no hard-tied enable; T07/T08 |
| GY-6180 VL6180X **or** VL53L0X carrier (choose one family) | 3 | [ ] | [ ] | [ ] | Downward left/right/center; three matching boards; 3.3 V VIN/host compatibility; T09 |
| TCA9548A carrier | 1 | [ ] | [ ] | [ ] | Required: channels 0/1/2, address 0x70; RESET pull-up; T03/T09 |
| ADS1115 (not ADS1015) | 1 | [ ] | [ ] | [ ] | 3.3 V supply, ADDR grounded for 0x48; battery A3 only, unused A0–A2 to GND; T03/T06 |
| PCF8574 / PCF8574A breakout | 1 | [ ] | [ ] | [ ] | 3.3 V, address 0x20 / 0x38, three address straps grounded; T03/T07 |
| MAX98357A amplifier breakout | 1 | [ ] | [ ] | [ ] | A = I²S; B uses a different data format; SD exposed, removable board pull-ups; T11 |
| Speaker, 4 Ω | 1 | [ ] | [ ] | [ ] | 3 W recommended if ordering; existing ~1 W requires measured power limit; T11 |
| Bumper microswitch with COM/NO/NC | 2 | [ ] | [ ] | [ ] | Both operate separately; choose NO parallel or optional NC series wiring; T10 |
| Rear skid / caster | 1 | [ ] | [ ] | [ ] | Stable support, no cable snag |
| BC547 NPN, Q1/Q2 | 2 + 1 spare | [ ] | [ ] | [ ] | Confirm actual manufacturer pinout; do not assume another NPN matches |

## Passive parts and construction

Used counts match the base circuit; ordering small packs is convenient. These are minimum fitted counts, not pack sizes.

| Item | Qty used | Have | Order | Tested | References / purpose |
| --- | ---: | :---: | :---: | :---: | --- |
| 100 kΩ resistors | 11 | [ ] | [ ] | [ ] | R1/R2 divider; R3–R6 pulldowns; R15/R16/R18/R19 inverter bias; R22 gain |
| 22 kΩ resistors | 2 | [ ] | [ ] | [ ] | R17/R20 enable pull-ups |
| 10 kΩ resistors | 2 + 1 if missing on mux | [ ] | [ ] | [ ] | R14 bumper, R21 fault; R25 mux RESET if not fitted |
| 470 Ω resistors | 1 | [ ] | [ ] | [ ] | R13 touch series |
| 4.7 kΩ resistors | As measured on upstream + 3 branches | [ ] | [ ] | [ ] | R23/R24 upstream I²C plus branch pull-ups only if absent; inspect carriers |
| 100 nF ceramic capacitors | 7 + missing module decoupling | [ ] | [ ] | [ ] | C2/C3/C4/C6/C8/C9/C14; add at each IC if breakout lacks them |
| 1000 µF electrolytic, ≥10 V | 1 | [ ] | [ ] | [ ] | C1 at driver VM; correct polarity; measure inrush |
| 100 µF electrolytic, ≥10 V | 1 | [ ] | [ ] | [ ] | C5 at amplifier |
| 10 µF capacitor | 1 | [ ] | [ ] | [ ] | C7 on 3V3 |
| 22–24 AWG flexible power wire | As needed | [ ] | [ ] | [ ] | Short battery, VM, amplifier and ground runs |
| 26–30 AWG signal wire | As needed | [ ] | [ ] | [ ] | Short I²C and analog wiring |
| Heat-shrink, insulated connectors, strain relief | Set | [ ] | [ ] | [ ] | No exposed battery or motor terminals |
| Perfboard + secure ToF/mux headers | Set | [ ] | [ ] | [ ] | GY-6180 is unsoldered; solder headers and inspect joints |
| Motor brackets, screws, chassis, sensor shrouds | Set | [ ] | [ ] | [ ] | ToF mounting trial ~30 mm (6180) / ~60 mm (530); validate lip and stopping margin |

## Optional improvements — order only if wanted or required by tests

| Item | Qty | Have | Order | Tested | When needed |
| --- | ---: | :---: | :---: | :---: | --- |
| Independent motor watchdog / power gate | Design needed | [ ] | [ ] | [ ] | Required before relying on unattended motion; no spare part purchase until circuit is engineered |

## Test equipment — borrow or order if missing

| Item | Qty | Have | Order | Tested | Purpose |
| --- | ---: | :---: | :---: | :---: | --- |
| Logic analyzer / oscilloscope | 1 | [ ] | [ ] | [ ] | PWM, bus rise time, resets, motor cutoff and brownout verification |
| Current-limited bench supply | 1 | [ ] | [ ] | [ ] | Required for controlled current characterization; borrow if missing |
| Multimeter with fused current input | 1 | [ ] | [ ] | [ ] | Required for polarity, rails, continuity, current and calibration |

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

Product choices: [GY-6180 VL6180X](https://robu.in/product/unsoldered-blue-gy-6180-vl6180x-light-sensor-distance-measurement-gesture-recognition-module/) or [VL53L0X](https://robu.in/product/vl53l0x-tof-based-lidar-laser-distance-sensor/). Order **three of one type**, not one of each. No GP2S sensors or LED drive components are needed.

Only after the final row passes: set `CALIBRATION_CONFIRMED = true`, rebuild, and perform supervised floor tests before any raised-table test.
