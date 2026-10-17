#pragma once
#include <Arduino.h>

// One I2C bus is shared by the safety task and the main loop.
// Hold a BusLock for every Wire transaction.
bool busBegin();

class BusLock {
 public:
  BusLock();
  ~BusLock();
  explicit operator bool() const { return held; }
  BusLock(const BusLock &) = delete;
  BusLock &operator=(const BusLock &) = delete;
 private:
  bool held;
};
