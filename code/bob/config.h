#pragma once
#include <Arduino.h>

// Canonical circuit and parts: docs/HARDWARE.md and docs/INVENTORY.md.
// Three downward ToF modules via TCA9548A; ADS1115 A3 measures battery only.

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
constexpr uint32_t I2C_HZ = 100000;  // PCF8574 is Standard-mode only
constexpr uint32_t BUS_LOCK_MS = 15;
constexpr uint32_t ADC_TIMEOUT_MS = 12;

// PCF8574 bits. Writing 0 turns a part ON; released (1) is always OFF.
constexpr uint8_t PCF_AMP = 1 << 1;     // Q1 -> MAX98357 SD
constexpr uint8_t PCF_DRIVER = 1 << 2;  // Q2 -> DRV8833 nSLEEP
constexpr uint8_t PCF_FAULT = 1 << 3;   // input: DRV8833 nFAULT, 0 = fault

// ---------- Calibration (from the tests) ----------
constexpr bool CALIBRATION_CONFIRMED = false;  // set true ONLY after docs/TESTING.md acceptance
constexpr bool BUMPER_NC_SERIES = false;  // existing NO parallel wiring; optional NC series upgrade
// All three edge modules must use the selected family. Do not mix sensor types.
#ifndef BOB_EDGE_SENSOR
#define BOB_EDGE_SENSOR 530  // fitted hardware: 3 x VL53L0X; legacy option: 6180
#endif
#if BOB_EDGE_SENSOR != 6180 && BOB_EDGE_SENSOR != 530
#error "BOB_EDGE_SENSOR must be 6180 or 530"
#endif
constexpr uint8_t EDGE_MUX_ADDR = 0x70;  // TCA9548A A0/A1/A2 grounded
constexpr uint8_t EDGE_CHANNELS[3] = {0, 1, 2}; // left, right, center
// Placeholder geometry only: replace with measured desk bounds before arming.
#if BOB_EDGE_SENSOR == 6180
constexpr uint16_t EDGE_MIN_MM[3] = {15, 15, 15};
constexpr uint16_t EDGE_MAX_MM[3] = {45, 45, 45};
#else
constexpr uint16_t EDGE_MIN_MM[3] = {40, 40, 40};
constexpr uint16_t EDGE_MAX_MM[3] = {80, 80, 80};
#endif
constexpr uint16_t EDGE_HYSTERESIS_MM = 3;
constexpr uint32_t EDGE_PERIOD_MS = 50;
constexpr uint32_t SENSOR_MAX_AGE_MS = 120;
constexpr uint32_t BATTERY_MAX_AGE_MS = 300;
constexpr uint32_t LINK_LEASE_MS = 1500;
constexpr uint32_t REQUEST_MAX_AGE_MS = 200;
constexpr bool LEFT_MOTOR_REVERSED = false;
constexpr bool RIGHT_MOTOR_REVERSED = false;
constexpr uint32_t TOUCH_IDLE = 30000;        // T05
constexpr uint32_t TOUCH_PRESS_DELTA = 10000;  // T05
constexpr uint32_t TOUCH_WAKE_DELTA = 8000;    // T05
constexpr float BATTERY_CAL = 1.000f;          // T06

// ---------- Limits ----------
constexpr float BATTERY_WARN_V = 3.50f;
constexpr float BATTERY_LOCK_V = 3.40f;   // motors refuse below this
constexpr float BATTERY_SLEEP_V = 3.30f;  // Bob sleeps if this low for BATTERY_SLEEP_MS
constexpr uint32_t BATTERY_SLEEP_MS = 10000;

constexpr int DUTY_CAP_PERCENT = 40;  // lower it after the Stage 4 floor test
constexpr uint32_t FORWARD_MAX_MS = 400;
constexpr uint32_t PIVOT_MAX_MS = 250;
constexpr uint32_t PATROL_FORWARD_MS = 200;
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
constexpr const char *FIRMWARE = "bob-3.0";
constexpr size_t MAX_TEXT_BYTES = 1024;
constexpr size_t MAX_PLAY_BYTES = 4096;
constexpr size_t MAX_IMAGE_BYTES = 512 * 1024;
static_assert(D0 == 1 && D1 == 2 && D2 == 3 && D3 == 4 && D4 == 5 && D5 == 6 &&
              D6 == 43 && D7 == 44 && D8 == 7 && D9 == 8 && D10 == 9,
              "Select XIAO_ESP32S3 (Sense), not the Plus or another board");
static_assert(PATROL_DUTY_PERCENT <= DUTY_CAP_PERCENT, "Patrol exceeds duty cap");

// Binary WebSocket frames start with one tag byte.
constexpr uint8_t TAG_MIC = 'A';    // Bob -> laptop, 16 kHz 16-bit mono PCM
constexpr uint8_t TAG_IMAGE = 'I';  // Bob -> laptop, JPEG
constexpr uint8_t TAG_PLAY = 'P';   // laptop -> Bob, 16 kHz 16-bit mono PCM
