// T07 — PCF8574 expander and the two safe switches
// Menu over Serial. Measure each enable line with a meter while you toggle it.
//   1  sensor LEDs   (P0, LED_K)        released = off
//   2  amplifier SD  (P1 -> Q1)         released = 0 V,  on = about 2.7 V
//   3  driver SLP    (P2 -> Q2)         released = 0 V,  on = about 3.2 V
//   f  read driver fault (P3)           1 = OK, 0 = fault
//   r  release all pins (0xFF)
// The motor inputs D2, D3, D8, D9 are held low, so the wheels cannot turn.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.

#include <Wire.h>

uint8_t PCF_ADDR = 0x20;  // changed to 0x38 automatically for a PCF8574A
constexpr uint8_t P_LEDS = 1 << 0, P_AMP = 1 << 1, P_DRIVER = 1 << 2, P_FAULT = 1 << 3;
uint8_t out = 0xFF;

bool pcfWrite(uint8_t v) {
  out = v | P_FAULT | 0xF0;  // P3 input and P4-P7 spare stay released
  Wire.beginTransmission(PCF_ADDR);
  Wire.write(out);
  return Wire.endTransmission() == 0;
}

int pcfRead() {
  if (Wire.requestFrom(PCF_ADDR, (uint8_t)1) != 1) return -1;
  return Wire.read();
}

void toggle(uint8_t bit, const char *name, const char *onText) {
  bool nowOn = out & bit;  // currently released -> turn on
  pcfWrite(nowOn ? (out & ~bit) : (out | bit));
  Serial.printf("%s: %s\n", name, nowOn ? onText : "OFF (released)");
}

void status() {
  int in = pcfRead();
  Serial.printf("out=0x%02X  LEDs %s, amp %s, driver %s, fault line %s\n", out, (out & P_LEDS) ? "off" : "ON",
                (out & P_AMP) ? "off" : "ON", (out & P_DRIVER) ? "asleep" : "AWAKE",
                in < 0 ? "read error" : (in & P_FAULT) ? "1 OK" : "0 FAULT");
}

void setup() {
  for (int p : {D2, D3, D8, D9}) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T07 PCF8574 and safe switches ===");
  Wire.begin();

  if (!pcfWrite(0xFF)) {
    PCF_ADDR = 0x38;
    if (!pcfWrite(0xFF)) {
      Serial.println("FAIL: no PCF8574 at 0x20 or 0x38. Run T03.");
      while (true) delay(1000);
    }
  }
  Serial.printf("PCF8574 at 0x%02X, all pins released.\n", PCF_ADDR);
  Serial.println("Released check with a meter: amp SD = 0 V, driver SLP = 0 V, sensor LEDs dark (phone camera).");
  Serial.println("Keys: 1 LEDs, 2 amp, 3 driver, f fault, r release all");
  status();
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  switch (c) {
    case '1': toggle(P_LEDS, "Sensor LEDs", "ON (look through a phone camera)"); break;
    case '2': toggle(P_AMP, "Amplifier SD", "ON - meter SD to GND, expect about 2.7 V"); break;
    case '3': toggle(P_DRIVER, "Driver SLP", "ON - meter SLP to GND, expect about 3.2 V"); break;
    case 'f': break;
    case 'r': pcfWrite(0xFF); Serial.println("All released."); break;
    default: return;
  }
  status();
}
