#include "pcf.h"
#include <Wire.h>
#include "bus.h"
#include "config.h"
static uint8_t shadow = 0xFF;
static bool known = false;
// Called with the bus held. Only ACKed writes update the cached latch.
static bool writeValue(uint8_t value) {
  value |= PCF_FAULT | 0xF1;
  Wire.beginTransmission(PCF_ADDR);
  Wire.write(value);
  if (Wire.endTransmission() != 0) { known = false; return false; }
  shadow = value;
  known = true;
  return true;
}
bool pcfBegin() { return pcfReleaseAll(); }
bool pcfReleaseAll() {
  BusLock lock;
  return lock && writeValue(0xFF);
}
bool pcfSet(uint8_t bit, bool on) {
  BusLock lock;
  if (!lock || !bit || (bit & ~(PCF_AMP | PCF_DRIVER))) return false;
  // Recover to off first after an uncertain write; never replay stale enables.
  if (!known && !writeValue(0xFF)) return false;
  uint8_t next = on ? (shadow & ~bit) : (shadow | bit);
  return writeValue(next);  // also detects an unplugged expander on repeated writes
}
bool pcfIsOn(uint8_t bit) {
  BusLock lock;
  return !lock || !known || !(shadow & bit);  // uncertainty requests a shutdown
}
bool pcfFaultActive() {
  BusLock lock;
  if (!lock || !known || Wire.requestFrom(PCF_ADDR, uint8_t(1)) != 1) return true;
  return !(Wire.read() & PCF_FAULT);
}
