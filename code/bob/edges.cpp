#include "sensors.h"
#include "bus.h"
#include "config.h"
#include "control.h"
#include <Wire.h>
#if BOB_EDGE_SENSOR == 6180
#include <VL6180X.h>
static VL6180X devices[3];
const char *edgeSensorName() { return "VL6180X"; }
#else
#include <VL53L0X.h>
static VL53L0X devices[3];
const char *edgeSensorName() { return "VL53L0X"; }
#endif
namespace {
constexpr uint8_t ADDRESS = 0x29, BUS_ERROR = 250, STALE = 251;
struct Channel {
  bool ready = false, valid = false, table = false;
  uint16_t mm = 0;
  uint8_t status = STALE;
  uint32_t pendingAt = 0, sampleAt = 0;
  control::EdgeFilter filter;
};
Channel channels[3];
// All mux operations and downstream transactions run under one bus lock.
bool select(uint8_t mask) {
  Wire.beginTransmission(EDGE_MUX_ADDR); Wire.write(mask);
  if (Wire.endTransmission() || Wire.requestFrom(EDGE_MUX_ADDR, uint8_t(1)) != 1) return false;
  return Wire.read() == mask;
}
void address(uint16_t reg) {
  Wire.beginTransmission(ADDRESS);
#if BOB_EDGE_SENSOR == 6180
  Wire.write(uint8_t(reg >> 8));
#endif
  Wire.write(uint8_t(reg));
}
bool readRangeReg(uint16_t reg, uint8_t *bytes, uint8_t count) {
  address(reg);
  if (Wire.endTransmission(false) || Wire.requestFrom(ADDRESS, count) != count) return false;
  for (uint8_t i=0; i<count; ++i) bytes[i] = Wire.read();
  return true;
}
bool writeRangeReg(uint16_t reg, uint8_t value) {
  address(reg); Wire.write(value); return Wire.endTransmission() == 0;
}
void invalidate(Channel &c, uint8_t status) {
  c.valid = c.table = false; c.status = status; c.filter.good = 0;
}
void poll(uint8_t i) {
  Channel &c = channels[i];
  if (!c.ready) { invalidate(c, BUS_ERROR); return; }
  BusLock lock;
  if (!lock) { invalidate(c, BUS_ERROR); return; }
  bool ok = select(1u << EDGE_CHANNELS[i]);
  uint8_t irq = 0;
#if BOB_EDGE_SENSOR == 6180
  if (ok) ok = readRangeReg(0x004F, &irq, 1);
  bool fresh = (irq & 7) == 4;
#else
  if (ok) ok = readRangeReg(0x13, &irq, 1);
  bool fresh = (irq & 7) == 4;
#endif
  if (ok && fresh) {
    uint8_t status = 0;
    uint16_t mm = 0;
#if BOB_EDGE_SENSOR == 6180
    uint8_t raw = 0;
    ok = readRangeReg(0x004D, &status, 1) && readRangeReg(0x0062, &raw, 1);
    status >>= 4; mm = raw;
    if (ok) ok = writeRangeReg(0x0015, 7);
    bool valid = status == 0 && mm <= 100;
#else
    uint8_t result[12] = {};
    ok = readRangeReg(0x14, result, sizeof(result));
    status = (result[0] >> 3) & 15; mm = uint16_t(result[10]) << 8 | result[11];
    if (ok) ok = writeRangeReg(0x0B, 1);
    bool valid = status == 11 && mm > 0 && mm < 2000;
#endif
    // A latched ready bit can hold an OLD frame. Never timestamp it as new.
    c.sampleAt = c.pendingAt;
    if (ok) c.pendingAt = millis(); // only an ACKed clear advances the acquisition boundary
    c.mm = mm; c.status = status;
    c.valid = ok && valid && !control::elapsed(millis(), c.sampleAt, SENSOR_MAX_AGE_MS);
    c.table = c.filter.update(c.valid, mm, EDGE_MIN_MM[i], EDGE_MAX_MM[i], EDGE_HYSTERESIS_MM);
  }
  // Leave all channels isolated even when a transaction failed.
  if (!select(0)) ok = false;
  if (!ok) invalidate(c, BUS_ERROR);
  else if (control::elapsed(millis(), c.sampleAt, SENSOR_MAX_AGE_MS)) invalidate(c, STALE);
}
}

bool edgesBegin() {
  bool all = true;
  for (uint8_t i=0; i<3; ++i) {
    channels[i] = Channel{};
    auto &c = channels[i];
    BusLock lock;
    if (!lock) { all = false; continue; }
    bool ok = EDGE_CHANNELS[i] < 8 && EDGE_MIN_MM[i] + 2*EDGE_HYSTERESIS_MM < EDGE_MAX_MM[i];
    for (uint8_t j=0; j<i; ++j) ok &= EDGE_CHANNELS[i] != EDGE_CHANNELS[j];
    if (ok) ok = select(1u << EDGE_CHANNELS[i]);
    uint8_t id = 0;
#if BOB_EDGE_SENSOR == 6180
    if (ok) ok = EDGE_MAX_MM[i] <= 100 && readRangeReg(0x0000, &id, 1) && id == 0xB4;
    if (ok) {
      devices[i].setTimeout(40);
      devices[i].init(); devices[i].configureDefault();
      ok = devices[i].last_status == 0 && writeRangeReg(0x001C, 30); // max convergence, ms
      if (ok) {
        // The sensor can still be running after an MCU-only reset. Stop first;
        // the library stop can trigger one ALS shot, so allow it to finish.
        devices[i].stopContinuous(); vTaskDelay(pdMS_TO_TICKS(200));
        ok = devices[i].last_status == 0 && writeRangeReg(0x0015, 7);
        if (ok) { devices[i].startRangeContinuous(EDGE_PERIOD_MS); ok = devices[i].last_status == 0; }
      }
    }
#else
    if (ok) ok = readRangeReg(0xC0, &id, 1) && id == 0xEE;
    if (ok) {
      devices[i].setTimeout(40);
      ok = devices[i].init() && devices[i].setMeasurementTimingBudget(33000);
      if (ok) {
        devices[i].stopContinuous(); vTaskDelay(pdMS_TO_TICKS(40));
        ok = devices[i].last_status == 0 && writeRangeReg(0x0B, 1);
        if (ok) { devices[i].startContinuous(EDGE_PERIOD_MS); ok = devices[i].last_status == 0; }
      }
    }
#endif
    c.pendingAt = millis() - SENSOR_MAX_AGE_MS; // discard the first possibly retained frame
    if (!select(0)) ok = false;
    c.ready = ok; all &= ok;
  }
  return all;
}
bool sensorsReadEdges(EdgeReading &out) {
  out = {}; out.ok = true; out.problem = "";
  uint32_t oldest = 0, now;
  for (uint8_t i=0; i<3; ++i) poll(i);
  now = millis();
  for (uint8_t i=0; i<3; ++i) {
    auto &c = channels[i];
    if (c.status != BUS_ERROR && control::elapsed(now, c.sampleAt, SENSOR_MAX_AGE_MS)) invalidate(c, STALE);
    out.mm[i] = c.mm; out.status[i] = c.status; out.valid[i] = c.valid; out.table[i] = c.table;
    oldest = max(oldest, uint32_t(now - c.sampleAt));
    if (!c.valid) { out.ok = false; out.problem = "ToF missing, invalid or stale"; }
  }
  out.sampleAt = now - oldest;
  return out.ok;
}
void edgesEnd() {
  for (uint8_t i=0; i<3; ++i) {
    BusLock lock;
    if (lock) {
      if (channels[i].ready && select(1u << EDGE_CHANNELS[i])) devices[i].stopContinuous();
      select(0);
    }
    channels[i] = Channel{};
  }
}
