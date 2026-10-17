#include "bus.h"
#include <Wire.h>
#include "config.h"
static SemaphoreHandle_t busMutex = nullptr;
bool busBegin() {
  busMutex = xSemaphoreCreateRecursiveMutex();
  if (!busMutex || !Wire.begin(D4, D5, I2C_HZ)) return false;
  Wire.setTimeOut(10);
  return true;
}
BusLock::BusLock() : held(busMutex && xSemaphoreTakeRecursive(busMutex, pdMS_TO_TICKS(BUS_LOCK_MS)) == pdTRUE) {}
BusLock::~BusLock() { if (held) xSemaphoreGiveRecursive(busMutex); }
