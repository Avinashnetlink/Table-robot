#pragma once
#include <cstdint>
inline bool fakeRangeInit=true, fakeRangeClear=true;
class VL53L0X {
 public:
  static constexpr uint8_t SYSTEM_INTERRUPT_CLEAR=0x0B;
  uint8_t last_status=0;
  void setTimeout(uint16_t) {}
  bool init() { return fakeRangeInit; }
  bool setMeasurementTimingBudget(uint32_t) { return true; }
  void startContinuous(uint32_t) { last_status=0; }
  void stopContinuous() {}
  void writeReg(uint8_t,uint8_t) { last_status=fakeRangeClear ? 0 : 2; }
};
