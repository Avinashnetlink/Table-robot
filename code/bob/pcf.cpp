// Connections: PCF8574 at 0x20 on D4 / D5, A0-A2 to GND.
// P0 sensor LED cathodes, P1 Q1 -> amp SD, P2 Q2 -> driver SLP, P3 <- driver FLT (R21 10k to 3V3).
#include "pcf.h"
#include <Wire.h>
#include "bus.h"
#include "config.h"

static uint8_t shadow = 0xFF;

static bool writeShadow() {
  BusLock lock;
  Wire.beginTransmission(PCF_ADDR);
  Wire.write(shadow | PCF_FAULT | 0xF0);  // P3 input and P4-P7 spare stay released
  return Wire.endTransmission() == 0;
}

bool pcfBegin() {
  shadow = 0xFF;
  return writeShadow();
}

bool pcfReleaseAll() {
  shadow = 0xFF;
  return writeShadow();
}

bool pcfSet(uint8_t bit, bool on) {
  BusLock lock;
  uint8_t next = on ? (shadow & ~bit) : (shadow | bit);
  if (next == shadow) return true;
  shadow = next;
  return writeShadow();
}

bool pcfIsOn(uint8_t bit) { return !(shadow & bit); }

bool pcfFaultActive() {
  BusLock lock;
  if (Wire.requestFrom(PCF_ADDR, (uint8_t)1) != 1) return true;
  return !(Wire.read() & PCF_FAULT);
}
