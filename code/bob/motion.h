#pragma once
#include <Arduino.h>

enum class Dir : uint8_t { Stop, Forward, PivotLeft, PivotRight };

const char *dirName(Dir d);
bool parseDir(const char *s, Dir &out);

// Low level. The safety task is the only caller of motionStart().
void motionBegin();                         // all four inputs low, 20 kHz PWM
bool motionStart(Dir d, int dutyPercent, uint32_t ms);  // also arms a one-shot stop timer
void motionStop();                          // safe from any task or the stop timer
bool motionActive();
Dir motionDir();
