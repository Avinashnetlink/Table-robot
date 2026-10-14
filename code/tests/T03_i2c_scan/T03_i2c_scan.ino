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
  return "unknown";
}

void scan() {
  Serial.println("\n--- scan ---");

  // With nothing driving the bus, both lines must rest high through the pull-ups.
  pinMode(SDA, INPUT);
  pinMode(SCL, INPUT);
  delay(2);
  bool sdaHigh = digitalRead(SDA), sclHigh = digitalRead(SCL);
  Serial.printf("SDA (D4) idle: %s   SCL (D5) idle: %s\n", sdaHigh ? "high OK" : "LOW",
                sclHigh ? "high OK" : "LOW");
  if (!sdaHigh || !sclHigh) {
    Serial.println("FAIL: a line is low. Missing pull-ups (fit R23/R24 4.7k), a short to GND, or a module unpowered.");
  }

  Wire.begin();
  Wire.setClock(100000);
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
  Wire.end();

  Serial.printf("%d device(s).\n", found);
  Serial.printf("OLED    0x3C : %s\n", oled ? "OK" : "missing");
  Serial.printf("ADS1115 0x48 : %s\n", ads ? "OK (ADDR to GND)" : "missing (ADDR must go to GND)");
  Serial.printf("PCF8574 0x20 : %s\n", pcf ? "OK" : "missing (A0-A2 must go to GND)");
  Serial.println(oled && ads && pcf ? "PASS" : "Not all parts found yet - fine if they are not wired yet.");
  Serial.println("Press Enter to scan again.");
}

void setup() {
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
