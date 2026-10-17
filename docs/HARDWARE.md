# Hardware and circuit — revision 3

Three **downward-facing ToF sensors replace the reflective edge sensors**. Fit three modules of one family: [Robu GY-6180 / VL6180X](https://robu.in/product/unsoldered-blue-gy-6180-vl6180x-light-sensor-distance-measurement-gesture-recognition-module/) or [Robu VL53L0X](https://robu.in/product/vl53l0x-tof-based-lidar-laser-distance-sensor/). The firmware supports either family, selected at build time. Do not mix them. These are edge sensors; there is no separate forward range sensor in this circuit. Obstacle contact is detected by the bumpers.

![Current circuit](../images/bob-wiring.png)

[Editable SVG](../images/bob-wiring.svg) · [Have/order checklist](INVENTORY.md) · [Calibration and tests](TESTING.md)

## ToF connections

Both sensor families use **7-bit address 0x29**. A **TCA9548A** at **0x70** selects one branch at a time. This avoids address collisions without consuming additional XIAO pins. Firmware verifies the selected channel and isolates all channels after access. See the [TI TCA9548A datasheet](https://www.ti.com/lit/ds/symlink/tca9548a.pdf).

| Connection | Destination |
| --- | --- |
| XIAO D4 / GPIO5 | Shared SDA: OLED, ADS1115, PCF8574, TCA9548A SDA |
| XIAO D5 / GPIO6 | Shared SCL: same devices; **100 kHz** |
| TCA9548A VCC / GND | XIAO 3V3 / common GND |
| TCA9548A A0, A1, A2 | GND, giving address 0x70 |
| TCA9548A RESET | 10 kΩ pull-up to 3V3 (R25); omit extra resistor if fitted on carrier |
| Mux SD0 / SC0 | Left sensor SDA / SCL |
| Mux SD1 / SC1 | Right sensor SDA / SCL |
| Mux SD2 / SC2 | Center sensor SDA / SCL |
| Each sensor carrier VIN/VCC / GND | 3V3 / common GND **after carrier compatibility check below** |
| Sensor XSHUT / GPIO0 / interrupt | No XIAO connection; enable must be held at the proper sensor-domain level by the carrier |
| Mux channels 3–7 | Unconnected |

Use the printed pin names, not a presumed physical header order. Do not connect the three sensor SDA/SCL pairs directly together. Each mux branch needs suitable pull-ups; inspect carrier resistors before adding more. The upstream bus and host-facing branches must stay at 3.3 V-compatible levels. Fit local 100 nF decoupling where a carrier lacks it. Keep wiring short and place the modules securely at the sensor lip.

The linked products identify the intended modules, but the pages did not expose a reliable carrier schematic during this review. **Check the delivered boards' regulator, pull-ups and level shifting before power.** The bare VL6180X operates at 2.6–3.0 V, so a bare IC or unregulated 2.8 V input must not be connected to 3V3. The circuit assumes a carrier that accepts 3.3 V at VIN and exposes compatible host I²C. Do not use 5 V pull-ups or connect XSHUT/GPIO pins blindly to 3V3. A carrier that requires 5 V input or lacks suitable translation needs a revised power/interface connection; the product name alone is insufficient evidence.

## Sensor selection and mounting

| Family | Build option | Initial mounting trial | Default desk band — **not calibration** |
| --- | --- | --- | --- |
| GY-6180 / VL6180X | `--edge-sensor vl6180x` (default) | Approximately 30 mm above the tabletop | 15–45 mm |
| VL53L0X | `--edge-sensor vl53l0x` | Approximately 60 mm above the tabletop | 40–80 mm |

[ST specifies VL6180X performance through 100 mm](https://www.st.com/resource/en/datasheet/vl6180x.pdf); longer reach is conditional. Firmware keeps its accepted desk band within 100 mm. VL53L0X has different close-range behavior; verify the selected height against [ST's sensor specification](https://www.st.com/resource/en/datasheet/vl53l0x.pdf) and actual module readings. Neither is a drop-in mechanical replacement at the old ~3 mm mounting height.

Point all three sensors vertically down. Start with the sensing line at least 25 mm ahead of the wheels, then validate `overhang > measured optical edge-transition offset + speed × worst detection latency + coast distance + margin`. The beam can still see the desk after its center passes the edge; measure that transition offset instead of treating the sensor as a point. Keep the optical field of view clear of chassis/wheels. Test glossy, dark, patterned and transparent surfaces, bright ambient light, tilt and mutual interference with all three sensors active. A nearby lower shelf or floor can return a plausible distance: reject any geometry where a drop still falls inside the calibrated desk band.

Each sensor runs continuously with a 50 ms period. Firmware polls without waiting for completion, checks native status and freshness, and requires three **new** in-band readings to reacquire a surface. Too near, too far, invalid, missing or stale data prevents movement. The oldest acquisition timestamp controls the motor's 120 ms lease; repeated polling of one frame cannot renew it. These are software targets, not measured stopping times. Pololu's VL53L0X driver does not implement ST's full sigma estimator; a plausible status is not proof that the surface is safe.

## XIAO ESP32-S3 Sense pins

| Pin / GPIO | Connection |
| --- | --- |
| D0 / 1 | Touch pad through R13 470 Ω |
| D1 / 2 | Bumpers; R14 10 kΩ to 3V3, C14 100 nF to GND |
| D2,D3 / 3,4 | DRV8833 AIN1,AIN2; each 100 kΩ to GND |
| D4,D5 / 5,6 | SDA,SCL as above |
| D6,D7 / 43,44 | MAX98357A BCLK,LRC |
| D8,D9 / 7,8 | DRV8833 BIN1,BIN2; each 100 kΩ to GND |
| D10 / 9 | MAX98357A DIN |
| Built-in microphone / 42,41 | PDM clock,data |
| Camera XCLK,PCLK,VSYNC,HREF,SDA,SCL | 10,13,38,47,40,39 |
| Camera D0–D7 | 15,17,18,16,14,12,11,48 |

Use the [Seeed Sense pinout](https://wiki.seeedstudio.com/xiao_esp32s3_pin_multiplexing/), not Plus. Leave microSD empty; isolate the matching expansion board's [J3 SD pull-ups](https://wiki.seeedstudio.com/xiao_esp32s3_sense_filesystem/) before using D8–D10. Confirm board revision and power-off continuity before cutting anything. Keep microphone jumpers intact. GPIO3's pulldown selects its JTAG strap state intentionally. Encoder wires remain insulated and unused.

## Power and battery

```text
protected 1S cell + -- F1 -- SW1 -- VBAT -- XIAO BAT+
                                  |----- MAX98357A VIN + C5/C6
                                  |----- R1 100k -- ADS A3 -- R2 100k -- GND
                                  |                   + C9 100nF to GND
                                  +-- SW2 motor kill -- DRV8833 VM + C1/C2
cell - ------------------------------- common GND / BAT-
XIAO 3V3 --> OLED, ADS1115, PCF8574, TCA9548A, compatible ToF carriers
```

ADS1115 stays at **0x48**, VDD=3V3, ADDR=GND, A3=battery divider. A0/A1/A2 are unused; tie them to GND. No XIAO analog pin is free, so removing the ADC would also remove battery monitoring or require another pin redesign. Battery full charge produces approximately 2.1 V at A3. Calibrate divider loading/tolerance at several voltages; the ±4.096 V ADC setting does not permit exceeding its supply. See [TI ADS1115](https://www.ti.com/lit/ds/symlink/ads1115.pdf).

Verify BAT polarity against the board markings and [Seeed guidance](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/). Use a protected 1S 4.2 V-charge cell with adequate measured current rating. Never feed VBAT into 3V3 or parallel chargers. F1 goes near the cell; choose its rating after load measurements and below all wire/switch/cell limits. SW1 does not isolate every source with USB attached; SW2 physically opens motor VM. Disconnect USB and cell for wiring. Keep SW2 open during charging/programming. Verify charger current and termination with motors/audio off.

C1=1000 µF + C2=100 nF at driver VM; C3/C4=100 nF across motor tabs; C5=100 µF + C6=100 nF at amplifier; C7=10 µF + C8=100 nF at 3V3. Observe polarity. Motor/amplifier power comes from VBAT, never 3V3. Route motor returns away from sensor returns. Measure combined startup current, 3V3 sag, cell sag and regulator heating with all three ToF modules active. A 5 V motor on a 1S cell has reduced torque; PWM duty is not a measured speed.

Battery software validates 2.5–4.30 V, warns below 3.50 V, locks motors below 3.40 V and requests sleep after 10 s below 3.30 V. No runtime or state-of-charge guarantee is inferred from voltage.

## Expander, motor, audio and bumper circuit

PCF8574 is **0x20** (PCF8574A alternative 0x38), VCC=3V3, address straps grounded. It limits the shared bus to [100 kHz](https://www.ti.com/lit/ds/symlink/pcf8574.pdf). OLED is 0x3C at 3V3. Combined upstream pull-ups of roughly 2.2–4.7 kΩ are a starting point, then verify rise time and current with the selected mux branch attached.

| PCF bit | Connection |
| --- | --- |
| P0 | **Unused, released high** |
| P1 | Q1 inverter → amplifier SD; write 0 to enable |
| P2 | Q2 inverter → driver nSLEEP; write 0 to enable |
| P3 | Driver nFAULT input, R21 10 kΩ to 3V3 |
| P4–P7 | Unused, released high |

Each inverter: PCF pin to 3V3 through 100 kΩ (R15/R18), PCF pin to NPN base through 100 kΩ (R16/R19), emitter to GND, collector to enable with 22 kΩ pull-up to 3V3 (R17/R20). Verify actual transistor pinouts and remove conflicting breakout straps. Measure off level and driver on ≥2.5 V; firmware allows 2 ms wake before PWM. See [DRV8833](https://www.ti.com/lit/ds/symlink/drv8833.pdf). PCF output latches survive MCU reset, so four external motor pulldowns remain essential.

MAX98357A GAIN uses R22 100 kΩ to VIN; speaker connects **only between OUT+ and OUT−**. Neither terminal goes to GND. The B variant uses a different data format. Verify output power/heating; amplitude limiting alone does not certify an existing 1 W speaker. See [MAX98357A/B](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf).

Default bumpers: two NO switches in parallel from D1 to GND. Optional `BUMPER_NC_SERIES=true`: two NC contacts in series from D1 to GND, allowing a broken wire to read unsafe. A ground short is still undetectable. Match T10's option to the actual circuit.

## Removed from revision 2

Remove all three GP2S700HCP devices, R7–R9 LED resistors, R10–R12 sensor resistors, C10–C13, and the LED_K/P0 wiring. The optional LED MOSFET circuit and forward-ToF circuit are removed. Do not combine old and new edge wiring. Remaining designators retain their numbers so existing motor/audio/battery wiring can be checked without renumbering.

Stopping uses all-low motor inputs (coast), then driver sleep. No reverse or automatic cliff escape is provided. Front sensing cannot prove side/rear support during a pivot. A full MCU/scheduler hang can defeat software deadlines until reset; unattended motion needs independent motor gating and appropriate coverage. All hardware acceptance remains pending.
