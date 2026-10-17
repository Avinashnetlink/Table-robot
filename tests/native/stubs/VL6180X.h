#pragma once
#include <cstdint>
inline bool fakeRangeInit=true;
class VL6180X {
 public:
  uint8_t last_status=0;
  void setTimeout(uint16_t) {}
  void init() { last_status=fakeRangeInit ? 0 : 2; }
  void configureDefault() {}
  void startRangeContinuous(uint32_t) { last_status=0; }
  void stopContinuous() {}
};
