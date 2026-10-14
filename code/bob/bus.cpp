// Connections: I2C SDA D4, SCL D5, shared by the OLED (0x3C), ADS1115 (0x48) and PCF8574 (0x20).
#include "bus.h"
#include <Wire.h>
#include "config.h"

static SemaphoreHandle_t busMutex = nullptr;

void busBegin() {
  busMutex = xSemaphoreCreateRecursiveMutex();
  Wire.begin();
  Wire.setClock(I2C_HZ);
  Wire.setTimeOut(20);
}

BusLock::BusLock() { xSemaphoreTakeRecursive(busMutex, portMAX_DELAY); }
BusLock::~BusLock() { xSemaphoreGiveRecursive(busMutex); }
