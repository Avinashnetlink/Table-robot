#pragma once
#include <Arduino.h>

// One I2C bus is shared by the safety task and the main loop.
// Hold a BusLock for every Wire transaction.
void busBegin();

class BusLock {
 public:
  BusLock();
  ~BusLock();
  BusLock(const BusLock &) = delete;
  BusLock &operator=(const BusLock &) = delete;
};
