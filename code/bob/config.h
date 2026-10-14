#pragma once
#include <Arduino.h>

/* =====================================================================
   BOB — COMPLETE CONNECTIONS (Seeed XIAO ESP32-S3 Sense)
   Same as Bob-pins.md and images/bob-wiring.png. Cut jumper J3 on the
   Sense board. Leave the microphone jumpers and the camera ribbon alone.
   =====================================================================

   POWER
     18650 (protected) +  -> SW1 power switch -> VBAT
     VBAT  -> XIAO BAT+ pad (the pad farther from USB)
     18650 -               -> XIAO BAT- pad (the pad nearer USB) = GND
     VBAT  -> DRV8833 VM    + C1 1000uF + C2 100nF to GND
     VBAT  -> MAX98357 VIN  + C5 100uF  + C6 100nF to GND
     VBAT  -> R1 100k -> A3 midpoint -> R2 100k -> GND, C9 100nF midpoint to GND
     XIAO 3V3 pin -> C7 10uF + C8 100nF to GND
     XIAO 3V3 -> OLED VCC, ADS1115 VDD, PCF8574 VCC, sensor LEDs and
                 collectors, every pull-up. Never to the DRV8833.

   XIAO PIN  GPIO   WIRE                               EXTRA PARTS
     D0      1      copper touch pad                   R13 470R in series, at the pin
     D1      2      both bumper switches (NO to COM)   R14 10k to 3V3, C14 100nF to GND
     D2      3      DRV8833 AIN1 (left motor)          R3 100k to GND
     D3      4      DRV8833 AIN2 (left motor)          R4 100k to GND
     D4      5      I2C SDA: OLED, ADS1115, PCF8574    R23 4.7k to 3V3 only if missing
     D5      6      I2C SCL: OLED, ADS1115, PCF8574    R24 4.7k to 3V3 only if missing
     D6      43     MAX98357 BCLK
     D7      44     MAX98357 LRC
     D8      7      DRV8833 BIN1 (right motor)         R5 100k to GND
     D9      8      DRV8833 BIN2 (right motor)         R6 100k to GND
     D10     9      MAX98357 DIN
     D11     42     built-in microphone clock (on board)
     D12     41     built-in microphone data  (on board)

   ADS1115 (0x48, ADDR to GND)
     A0  front-left  GP2S700HCP emitter   R10 10k to GND, C10 100nF to GND
     A1  front-right GP2S700HCP emitter   R11 10k to GND, C11 100nF to GND
     A2  front-center GP2S700HCP emitter  R12 10k to GND, C12 100nF to GND
     A3  battery divider midpoint (R1/R2, C9)

   GP2S700HCP x3 (check pad numbers against your datasheet)
     pad 4 LED anode    -> R7 / R8 / R9 470R -> 3V3
     pad 3 LED cathode  -> LED_K line (all three joined) -> PCF8574 P0
     pad 2 collector    -> 3V3   (C13 100nF 3V3 to GND on the sensor lip)
     pad 1 emitter      -> ADS1115 A0 / A1 / A2

   PCF8574 (0x20, A0 A1 A2 to GND; PCF8574A is 0x38)
     P0  LED_K, the three sensor LED cathodes        write 0 = LEDs on
     P1  Q1 safe switch -> MAX98357 SD               write 0 = amp on
     P2  Q2 safe switch -> DRV8833 SLP (nSLEEP)      write 0 = driver awake
     P3  DRV8833 FLT (nFAULT), R21 10k to 3V3         input, 0 = fault
     P4-P7 spare

   SAFE SWITCH, built twice (Q1 for P1, Q2 for P2), BC547 C-B-E
     Pn -> R15 / R18 100k -> 3V3
     Pn -> R16 / R19 100k -> BC547 base;  emitter -> GND
     BC547 collector -> enable wire (SD or SLP) -> R17 / R20 22k -> 3V3

   DRV8833 module (no logic supply pin)
     VM VBAT, GND, AIN1 D2, AIN2 D3, BIN1 D8, BIN2 D9, SLP Q2, FLT P3
     AOUT1/AOUT2 left motor  + C3 100nF across its tabs
     BOUT1/BOUT2 right motor + C4 100nF across its tabs

   MAX98357A
     VIN VBAT, GND, BCLK D6, LRC D7, DIN D10, SD Q1,
     GAIN -> R22 100k -> VIN (3 dB), OUT+ / OUT- speaker only, never GND

   OLED SSD1306 (0x3C): VCC 3V3, GND, SDA D4, SCL D5
   ===================================================================== */

// ---------- Pins ----------
constexpr uint8_t PIN_TOUCH = D0;   // GPIO1, touch 1, through R13 470R
constexpr uint8_t PIN_BUMPER = D1;  // R14 10k pull-up, pressed = LOW
constexpr uint8_t PIN_AIN1 = D2;    // left motor
constexpr uint8_t PIN_AIN2 = D3;
constexpr uint8_t PIN_BIN1 = D8;    // right motor (J3 cut)
constexpr uint8_t PIN_BIN2 = D9;
constexpr uint8_t PIN_I2S_BCLK = D6;
constexpr uint8_t PIN_I2S_LRC = D7;
constexpr uint8_t PIN_I2S_DOUT = D10;
constexpr uint8_t PIN_MIC_CLK = 42;
constexpr uint8_t PIN_MIC_DATA = 41;

// ---------- I2C ----------
constexpr uint8_t OLED_ADDR = 0x3C;
constexpr uint8_t ADS_ADDR = 0x48;
constexpr uint8_t PCF_ADDR = 0x20;  // 0x38 for a PCF8574A
constexpr uint32_t I2C_HZ = 400000;

// PCF8574 bits. Writing 0 turns a part ON; released (1) is always OFF.
constexpr uint8_t PCF_LEDS = 1 << 0;    // sensor LED cathodes
constexpr uint8_t PCF_AMP = 1 << 1;     // Q1 -> MAX98357 SD
constexpr uint8_t PCF_DRIVER = 1 << 2;  // Q2 -> DRV8833 nSLEEP
constexpr uint8_t PCF_FAULT = 1 << 3;   // input: DRV8833 nFAULT, 0 = fault

// ---------- Calibration (from the tests) ----------
constexpr uint32_t TOUCH_IDLE = 30000;        // T05
constexpr uint32_t TOUCH_PRESS_DELTA = 10000;  // T05
constexpr uint32_t TOUCH_WAKE_DELTA = 8000;    // T05
constexpr float BATTERY_CAL = 1.000f;          // T06
constexpr float EDGE_THRESHOLD_V[3] = {0.300f, 0.300f, 0.300f};  // T09: left, right, center

// ---------- Limits ----------
constexpr float BATTERY_WARN_V = 3.50f;
constexpr float BATTERY_LOCK_V = 3.40f;   // motors refuse below this
constexpr float BATTERY_SLEEP_V = 3.30f;  // Bob sleeps if this low for BATTERY_SLEEP_MS
constexpr uint32_t BATTERY_SLEEP_MS = 10000;
constexpr float SENSOR_SATURATED_V = 3.20f;  // LEDs-on reading this high = bad sensor
constexpr float SENSOR_AMBIENT_MAX_V = 1.00f;  // LEDs-off reading this high = too much room light

constexpr int DUTY_CAP_PERCENT = 40;  // lower it after the Phase 5 floor test
constexpr uint32_t FORWARD_MAX_MS = 400;
constexpr uint32_t PIVOT_MAX_MS = 250;
constexpr uint32_t PATROL_FORWARD_MS = 200;
constexpr uint32_t PATROL_PIVOT_MS = 150;
constexpr int PATROL_DUTY_PERCENT = 30;
constexpr uint32_t PATROL_PAUSE_MS = 150;  // look again between steps

constexpr uint32_t PWM_HZ = 20000;
constexpr uint8_t PWM_BITS = 10;

// ---------- Timing ----------
constexpr uint32_t UNLOCK_HOLD_MS = 2000;
constexpr uint32_t SLEEP_AFTER_MS = 60000;
constexpr uint32_t STATUS_EVERY_MS = 2000;
constexpr uint32_t WDT_TIMEOUT_MS = 5000;
constexpr uint32_t SPEAKER_IDLE_MS = 400;     // amp turns off after this much silence
constexpr uint32_t MIC_AFTER_SPEAK_MS = 300;  // mic stays muted this long after speaking

// ---------- Audio ----------
constexpr int AUDIO_RATE = 16000;
constexpr int MIC_CHUNK_SAMPLES = AUDIO_RATE / 25;  // 40 ms

// ---------- Network ----------
constexpr uint16_t SERVER_PORT = 8765;
constexpr const char *SERVER_PATH = "/bob";
constexpr const char *FIRMWARE = "bob-1.0";

// Binary WebSocket frames start with one tag byte.
constexpr uint8_t TAG_MIC = 'A';    // Bob -> laptop, 16 kHz 16-bit mono PCM
constexpr uint8_t TAG_IMAGE = 'I';  // Bob -> laptop, JPEG
constexpr uint8_t TAG_PLAY = 'P';   // laptop -> Bob, 16 kHz 16-bit mono PCM
