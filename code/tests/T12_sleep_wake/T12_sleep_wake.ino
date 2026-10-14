// T12 — Deep sleep, then wake only by touching the pad
// Counts down 20 s on the OLED, releases every PCF8574 pin, turns the OLED off,
// and deep-sleeps. Measure the battery current while it sleeps. Touch the pad
// to wake it; the boot count and wake reason are printed and shown.
//
// Set TOUCH_WAKE_DELTA from T05 first.
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.
// Libraries: Adafruit SSD1306, Adafruit GFX Library.

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "esp_sleep.h"

constexpr uint8_t PIN_TOUCH = D0;
constexpr uint32_t TOUCH_WAKE_DELTA = 8000;  // from T05
constexpr uint32_t SLEEP_AFTER_S = 20;

RTC_DATA_ATTR uint32_t bootCount = 0;
Adafruit_SSD1306 display(128, 64, &Wire, -1);
bool haveDisplay = false;

void pcfReleaseAll() {
  for (uint8_t addr : {0x20, 0x38}) {
    Wire.beginTransmission(addr);
    Wire.write(0xFF);
    Wire.endTransmission();
  }
}

const char *wakeReason() {
  switch (esp_sleep_get_wakeup_cause()) {
    case ESP_SLEEP_WAKEUP_TOUCHPAD: return "touch pad";
    case ESP_SLEEP_WAKEUP_UNDEFINED: return "power on / reset";
    default: return "other";
  }
}

void show(const char *a, const char *b) {
  if (!haveDisplay) return;
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(2);
  display.setCursor(0, 8);
  display.print(a);
  display.setTextSize(1);
  display.setCursor(0, 40);
  display.print(b);
  display.display();
}

void setup() {
  for (int p : {D2, D3, D8, D9}) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }
  Serial.begin(115200);
  delay(1500);
  bootCount++;
  Wire.begin();
  pcfReleaseAll();
  haveDisplay = display.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  Serial.printf("\n=== T12 sleep and touch wake ===\nBoot %lu, woke by: %s\n", (unsigned long)bootCount, wakeReason());
  char line[32];
  snprintf(line, sizeof(line), "boot %lu: %s", (unsigned long)bootCount, wakeReason());
  show("Hello!", line);
  delay(2000);

  for (int s = SLEEP_AFTER_S; s > 0; s--) {
    snprintf(line, sizeof(line), "Sleep in %d s", s);
    show("Awake", line);
    Serial.println(line);
    delay(1000);
  }

  Serial.println("Sleeping. Measure battery current now. Say 'Hey Bob' - nothing must happen. Then touch the pad.");
  Serial.flush();
  if (haveDisplay) display.ssd1306_command(SSD1306_DISPLAYOFF);
  pcfReleaseAll();  // LEDs, amp and driver off
  touchSleepWakeUpEnable(PIN_TOUCH, TOUCH_WAKE_DELTA);
  esp_deep_sleep_start();
}

void loop() {}
