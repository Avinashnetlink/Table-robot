// T03 — I2C bus scan
// Checks the SDA / SCL pull-ups, then lists every device and names Bob's three:
// OLED 0x3C, ADS1115 0x48, PCF8574 0x20 (or PCF8574A 0x38).
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.

#include <Wire.h>

const char *deviceName(uint8_t a) {
  if (a == 0x3C || a == 0x3D) return "SSD1306 OLED";
  if (a >= 0x48 && a <= 0x4B) return "ADS1115 ADC";
  if (a >= 0x20 && a <= 0x27) return "PCF8574 expander";
  if (a >= 0x38 && a <= 0x3B) return "PCF8574A expander";
  if (a == 0x70) return "TCA9548A edge mux";
  if (a == 0x29) return "ToF edge sensor";
  return "unknown";
}

void scan() {
  Serial.println("\n--- scan ---");

  Wire.begin(D4, D5, 100000); Wire.setTimeOut(10);
  Wire.beginTransmission(0x70); Wire.write(0); Wire.endTransmission();
  bool oled = false, ads = false, pcf = false;
  int found = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  0x%02X  %s\n", a, deviceName(a));
      found++;
      if (a == 0x3C || a == 0x3D) oled = true;
      if (a == 0x48) ads = true;
      if (a == 0x20 || a == 0x38) pcf = true;
    }
  }
  bool edges = true;
  for (uint8_t ch=0; ch<3; ++ch) {
    Wire.beginTransmission(0x70); Wire.write(uint8_t(1u<<ch));
    bool ok = Wire.endTransmission()==0;
    if (ok) { Wire.beginTransmission(0x29); ok=Wire.endTransmission()==0; }
    Serial.printf("Mux CH%u ToF 0x29: %s\n", ch, ok ? "ACK (identity checked by firmware)" : "MISSING");
    edges &= ok;
  }
  Wire.beginTransmission(0x70); Wire.write(0); Wire.endTransmission();
  Wire.end();

  Serial.printf("%d device(s).\n", found);
  Serial.printf("OLED    0x3C : %s\n", oled ? "OK" : "missing");
  Serial.printf("ADS1115 0x48 : %s\n", ads ? "OK (ADDR to GND)" : "missing (ADDR must go to GND)");
  Serial.printf("PCF8574 0x20 : %s\n", pcf ? "OK" : "missing (A0-A2 must go to GND)");
  Serial.println(oled && ads && pcf && edges ? "PASS" : "Not all parts found yet - fine if they are not wired yet.");
  Serial.println("Press Enter to scan again.");
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
  Serial.println("\n=== T03 I2C scan ===");
  scan();
}

void loop() {
  if (Serial.available()) {
    while (Serial.available()) Serial.read();
    scan();
  }
}
