#pragma once
#include <Arduino.h>

enum class TouchEvent : uint8_t { None, Tap, Hold };

void touchBegin();
TouchEvent touchService();  // call every loop; Hold fires once after UNLOCK_HOLD_MS
bool touchDown();

const char *wakeReason();
[[noreturn]] void powerSleepNow();  // everything off, wake on the touch pad only
