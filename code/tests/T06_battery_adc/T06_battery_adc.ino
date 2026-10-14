// T06 — Battery voltage through the ADS1115
// Reads A3 (R1/R2 divider midpoint) and prints the cell voltage once a second.
// Type the voltage your multimeter shows at the battery (for example 3.98)
// and press Enter: the sketch prints BATTERY_CAL for code/bob/config.h.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.
// Library: Adafruit ADS1X15.

#include <Wire.h>
#include <Adafruit_ADS1X15.h>

constexpr float DIVIDER = 2.0f;  // R1 = R2 = 100k
constexpr float WARN_V = 3.5f, LOCK_V = 3.4f;

Adafruit_ADS1115 ads;
float lastRaw = 0;

float readCellRaw() {
  const int n = 8;
  float sum = 0;
  for (int i = 0; i < n; i++) sum += ads.computeVolts(ads.readADC_SingleEnded(3));
  return sum / n * DIVIDER;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T06 battery and ADS1115 ===");
  Wire.begin();
  if (!ads.begin(0x48)) {
    Serial.println("FAIL: no ADS1115 at 0x48. Check VDD 3V3, GND, ADDR to GND, SDA D4, SCL D5.");
    while (true) delay(1000);
  }
  ads.setGain(GAIN_ONE);  // +/-4.096 V
  ads.setDataRate(RATE_ADS1115_128SPS);
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
  float a0 = ads.computeVolts(ads.readADC_SingleEnded(0));
  float a1 = ads.computeVolts(ads.readADC_SingleEnded(1));
  float a2 = ads.computeVolts(ads.readADC_SingleEnded(2));
  const char *state = lastRaw < LOCK_V ? "LOCK motors" : lastRaw < WARN_V ? "WARN low" : "OK";
  Serial.printf("cell %.3f V  [%s]   A0 %.3f  A1 %.3f  A2 %.3f\n", lastRaw, state, a0, a1, a2);
  if (lastRaw < 0.3f) Serial.println("  A3 reads ~0: divider not connected, or power switch off.");
  delay(1000);
}
