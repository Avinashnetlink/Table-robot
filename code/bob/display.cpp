// Connections: SSD1306 OLED at 0x3C. VCC 3V3, GND, SDA D4, SCL D5.
#include "display.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>
#include "bus.h"
#include "config.h"

static Adafruit_SSD1306 oled(128, 64, &Wire, -1, I2C_HZ, I2C_HZ);
static uint16_t cursor = 1024;
static bool ok = false;
static char text1[22] = "", text2[22] = "";
static uint32_t textUntil = 0;
static char mood[12] = "awake";
static uint32_t lastDraw = 0;
static uint32_t lastHash = 0;

bool displayBegin() {
  BusLock lock;
  if (!lock) return false;
  Wire.beginTransmission(OLED_ADDR);
  if (Wire.endTransmission() != 0) return false;
  ok = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR, true, false);
  if (ok) {
    oled.clearDisplay();
    oled.display();
  }
  return ok;
}

void displaySetText(const char *line1, const char *line2, uint32_t holdMs) {
  strlcpy(text1, line1 ? line1 : "", sizeof(text1));
  strlcpy(text2, line2 ? line2 : "", sizeof(text2));
  textUntil = millis() + min(holdMs, uint32_t(60000));
}

void displaySetMood(const char *state) { strlcpy(mood, state, sizeof(mood)); }

static void drawEyes(bool blink) {
  const int y = 14;
  if (blink || !strcmp(mood, "thinking")) {
    oled.fillRect(30, y + 10, 20, 3, SSD1306_WHITE);
    oled.fillRect(78, y + 10, 20, 3, SSD1306_WHITE);
  } else if (!strcmp(mood, "listening")) {
    oled.drawCircle(40, y + 11, 10, SSD1306_WHITE);
    oled.drawCircle(88, y + 11, 10, SSD1306_WHITE);
    oled.fillCircle(40, y + 11, 5, SSD1306_WHITE);
    oled.fillCircle(88, y + 11, 5, SSD1306_WHITE);
  } else {
    oled.fillRoundRect(31, y, 18, 22, 6, SSD1306_WHITE);
    oled.fillRoundRect(79, y, 18, 22, 6, SSD1306_WHITE);
  }
  if (!strcmp(mood, "speaking")) oled.drawRoundRect(52, y + 28, 24, 6, 3, SSD1306_WHITE);
}

// A full 1 KB frame at 100 kHz takes ~100 ms. Send only 64 bytes per loop,
// yielding the bus to the safety task between chunks. Explicit page addressing.
static bool pump() {
  if (cursor >= 1024) return false;
  BusLock lock;
  if (!lock) return true;
  Wire.beginTransmission(OLED_ADDR);
  Wire.write(0x00); Wire.write(0x21); Wire.write(cursor % 128); Wire.write(cursor % 128 + 63);
  Wire.write(0x22); Wire.write(cursor / 128); Wire.write(cursor / 128);
  if (Wire.endTransmission() != 0) { ok = false; return true; }
  Wire.beginTransmission(OLED_ADDR); Wire.write(0x40);
  Wire.write(oled.getBuffer() + cursor, 64);
  if (Wire.endTransmission() != 0) { ok = false; return true; }
  cursor += 64;
  return cursor < 1024;
}

void displayUpdate(float battery, bool batteryWarn, bool wifi, bool unlocked, bool patrol) {
  if (!ok) return;
  if (pump()) return;
  uint32_t now = millis();
  bool showText = int32_t(textUntil - now) > 0 && (text1[0] || text2[0]);
  bool blink = (now / 250) % 16 == 0;

  // Redraw only when something visible changed, at most 5 times a second.
  uint32_t hash = 2166136261u;
  auto mix = [&hash](uint32_t v) { hash = (hash ^ v) * 16777619u; };
  auto mixText = [&mix](const char *s) { while (*s) mix((uint8_t)*s++); };
  mix((uint32_t)(battery * 100));
  mix(batteryWarn | wifi << 1 | unlocked << 2 | patrol << 3 | showText << 4 | blink << 5);
  mixText(mood);
  if (showText) {
    mixText(text1);
    mixText(text2);
  }
  if (hash == lastHash && now - lastDraw < 2000) return;
  if (now - lastDraw < 200) return;
  lastHash = hash;
  lastDraw = now;

  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);

  // Top bar: Wi-Fi, lock, patrol, battery
  oled.setCursor(0, 0);
  oled.print(wifi ? "WiFi" : "Offline");
  oled.setCursor(48, 0);
  oled.print(patrol ? "PATROL" : unlocked ? "drive" : "lock");
  oled.setCursor(92, 0);
  if (battery > 0.5f) oled.printf("%s%.2f", batteryWarn ? "!" : "", battery);

  if (showText) {
    oled.setCursor(0, 22);
    oled.setTextSize(strlen(text1) <= 10 ? 2 : 1);
    oled.print(text1);
    oled.setTextSize(1);
    oled.setCursor(0, 48);
    oled.print(text2);
  } else {
    drawEyes(blink);
    oled.setCursor(0, 56);
    oled.print(mood);
  }
  cursor = 0;
}

void displayOff() {
  if (!ok) return;
  BusLock lock;
  if (!lock) return;
  cursor = 1024;
  oled.ssd1306_command(SSD1306_DISPLAYOFF);
}
