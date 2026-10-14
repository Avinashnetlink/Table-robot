// T04 — 0.96" SSD1306 OLED
// Shows "Bob", a face that blinks, and a counter.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.
// Libraries: Adafruit SSD1306, Adafruit GFX Library.

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void drawFace(bool eyesOpen, uint32_t n) {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(2);
  display.setCursor(46, 0);
  display.print("Bob");

  if (eyesOpen) {
    display.fillRoundRect(34, 24, 16, 20, 5, SSD1306_WHITE);
    display.fillRoundRect(78, 24, 16, 20, 5, SSD1306_WHITE);
  } else {
    display.fillRect(34, 33, 16, 3, SSD1306_WHITE);
    display.fillRect(78, 33, 16, 3, SSD1306_WHITE);
  }

  display.setTextSize(1);
  display.setCursor(0, 56);
  display.printf("T04 OLED   %lu", (unsigned long)n);
  display.display();
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T04 OLED ===");
  Wire.begin();

  uint8_t addr = 0x3C;
  if (!display.begin(SSD1306_SWITCHCAPVCC, addr)) {
    addr = 0x3D;
    if (!display.begin(SSD1306_SWITCHCAPVCC, addr)) {
      Serial.println("FAIL: no OLED at 0x3C or 0x3D. Check VCC 3V3, GND, SDA D4, SCL D5. Run T03.");
      while (true) delay(1000);
    }
  }
  Serial.printf("OLED found at 0x%02X. PASS if the screen shows Bob and blinks.\n", addr);
}

void loop() {
  static uint32_t n = 0;
  n++;
  drawFace(n % 8 != 0, n);
  delay(300);
}
