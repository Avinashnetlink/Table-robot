#include "sensors.h"
#include <Wire.h>
#include "bus.h"
#include "config.h"
#include "control.h"
static bool adsOk = false;

// ADS1115 single-shot at +/-4.096 V, 860 SPS, comparator disabled.
// Avoid the library's unbounded conversion-ready loop and ignored I2C errors.
static bool writeReg(uint8_t reg, uint16_t value) {
  BusLock lock;
  if (!lock) return false;
  Wire.beginTransmission(ADS_ADDR);
  Wire.write(reg); Wire.write(uint8_t(value >> 8)); Wire.write(uint8_t(value));
  return Wire.endTransmission() == 0;
}
static bool readReg(uint8_t reg, uint16_t &value) {
  BusLock lock;
  if (!lock) return false;
  Wire.beginTransmission(ADS_ADDR); Wire.write(reg);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(ADS_ADDR, uint8_t(2)) != 2) return false;
  value = uint16_t(Wire.read()) << 8; value |= Wire.read();
  return true;
}
static bool readChannel(uint8_t ch, float &volts) {
  const uint16_t config = 0x8000 | ((4 + ch) << 12) | 0x0200 | 0x0100 | 0x00E0 | 0x0003;
  if (!writeReg(1, config)) return false;
  uint32_t start = millis();
  do {
    vTaskDelay(pdMS_TO_TICKS(1));
    uint16_t status;
    if (!readReg(1, status) || (status & 0x7FFF) != (config & 0x7FFF)) return false;
    if (status & 0x8000) {
      uint16_t raw;
      if (!readReg(0, raw)) return false;
      volts = int16_t(raw) * 0.000125f;
      return volts >= -0.02f && volts <= 3.30f;
    }
  } while (!control::elapsed(millis(), start, ADC_TIMEOUT_MS));
  return false;
}
bool sensorsBegin() {
  uint16_t reg;
  adsOk = readReg(1, reg);
  return adsOk;
}
bool sensorsReadBattery(float &volts) {
  float midpoint;
  if (!adsOk || !readChannel(3, midpoint)) return false;
  volts = midpoint * 2.0f * BATTERY_CAL;
  return control::batteryValid(volts);
}
