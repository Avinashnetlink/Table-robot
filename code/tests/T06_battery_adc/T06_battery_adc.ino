// T06 — Battery voltage through the ADS1115
// Reads A3 (R1/R2 divider midpoint) and prints the cell voltage once a second.
// Type the voltage your multimeter shows at the battery (for example 3.98)
// and press Enter: the sketch prints BATTERY_CAL for code/bob/config.h.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.
// Checked ADS1115 register access; no external ADC library.

#include <Wire.h>
#include <math.h>

constexpr float DIVIDER = 2.0f;  // R1 = R2 = 100k
constexpr float WARN_V = 3.5f, LOCK_V = 3.4f;


static float readVolts(uint8_t channel) {
  const uint16_t config = 0x8000 | ((4 + channel) << 12) | 0x0200 | 0x0100 | 0x00E0 | 3;
  Wire.beginTransmission(0x48); Wire.write(1); Wire.write(uint8_t(config >> 8)); Wire.write(uint8_t(config));
  if (Wire.endTransmission()) return NAN;
  uint32_t start = millis();
  do {
    delay(1);
    Wire.beginTransmission(0x48); Wire.write(1);
    if (Wire.endTransmission(false) || Wire.requestFrom(uint8_t(0x48), uint8_t(2)) != 2) return NAN;
    uint16_t status = uint16_t(Wire.read()) << 8; status |= Wire.read();
    if ((status & 0x7FFF) != (config & 0x7FFF)) return NAN;
    if (status & 0x8000) {
      Wire.beginTransmission(0x48); Wire.write(0);
      if (Wire.endTransmission(false) || Wire.requestFrom(uint8_t(0x48), uint8_t(2)) != 2) return NAN;
      uint16_t raw = uint16_t(Wire.read()) << 8; raw |= Wire.read();
      return int16_t(raw) * 0.000125f;
    }
  } while (uint32_t(millis() - start) < 12);
  return NAN;
}

float lastRaw = 0;

float readCellRaw() {
  const int n = 8;
  float sum = 0;
  for (int i = 0; i < n; i++) sum += readVolts(3);
  return sum / n * DIVIDER;
}


// Reset the retained expander latch BEFORE any startup delay.
static void benchSafeBoot() {
  for (int p : {D2, D3, D8, D9}) { digitalWrite(p, LOW); pinMode(p, OUTPUT); }
  Wire.begin(D4, D5, 100000); Wire.setTimeOut(10);
  for (uint8_t a : {0x20, 0x38}) {
    Wire.beginTransmission(a); Wire.write(0xFF); Wire.endTransmission();
  }
}

void setup() {
  benchSafeBoot();
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T06 battery and ADS1115 ===");
  Wire.begin();
  Wire.beginTransmission(0x48);
  if (Wire.endTransmission()) {
    Serial.println("FAIL: no ADS1115 at 0x48. Check VDD 3V3, GND, ADDR to GND, SDA D4, SCL D5.");
    while (true) delay(1000);
  }
  Serial.println("Measure the switched battery with a meter. Type the meter value and press Enter.");
}

void loop() {
  if (Serial.available()) {
    float meter = Serial.parseFloat();
    while (Serial.available()) Serial.read();
    if (meter > 2.5f && meter < 4.5f && lastRaw > 0.5f) {
      float cal = meter / lastRaw;
      Serial.printf("\nMeter %.3f V, ADC %.3f V -> error %+.0f mV\n", meter, lastRaw, (lastRaw - meter) * 1000);
      Serial.printf("Copy into code/bob/config.h:\n  constexpr float BATTERY_CAL = %.4f;\n\n", cal);
      Serial.println(fabsf(lastRaw - meter) < 0.05f ? "PASS - within 50 mV" : "Use BATTERY_CAL to correct it.");
    }
  }

  lastRaw = readCellRaw();
  if (!isfinite(lastRaw)) { Serial.println("FAIL: ADC error/timeout, do not calibrate"); delay(100); return; }
  const char *state = lastRaw < LOCK_V ? "LOCK motors" : lastRaw < WARN_V ? "WARN low" : "OK";
  Serial.printf("cell %.3f V  [%s]\n", lastRaw, state);
  if (lastRaw < 0.3f) Serial.println("  A3 reads ~0: divider not connected, or power switch off.");
  delay(1000);
}
