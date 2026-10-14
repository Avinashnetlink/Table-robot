#pragma once
#include <Arduino.h>
#include "motion.h"

struct SafetySnapshot {
  float battery;
  bool batteryValid, batteryOk, batteryWarn;
  bool sensorsOk;
  bool table[3];  // left, right, center
  float edgeV[3];
  bool bumper, fault;
  bool moving;
  Dir dir;
  bool patrol, unlocked, speaking;
  uint32_t cycles;  // sensor cycles completed
};

struct SafetyEvent {
  const char *what;    // "move_result", "stopped", "bumper", "fault", "sensor", "battery", "patrol"
  const char *detail;  // reason, always a string literal
  bool ok;
};

// The safety task runs on its own, reads every sensor about every 25 ms,
// and is the only code that starts the motors.
void safetyBegin();
void safetySuspend();  // before deep sleep: motors off, task stops using I2C

SafetySnapshot safetyGet();
bool safetyPopEvent(SafetyEvent &e);

bool safetyRequestMove(Dir d, int dutyPercent, uint32_t ms);  // result arrives as a "move_result" event
void safetyStopAll(const char *why);  // motors off and patrol off, immediately
void safetySetPatrol(bool on);
void safetySetUnlocked(bool on);
void safetySetSpeaking(bool on);  // no motion while the speaker plays
