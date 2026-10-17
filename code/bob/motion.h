#pragma once
#include <Arduino.h>
#include "control.h"

const char *dirName(Dir d);
bool parseDir(const char *s, Dir &out);

// Low level. The safety task is the only caller of motionStart().
bool motionBegin();                         // all four inputs low, 20 kHz PWM
bool motionStart(Dir d, int dutyPercent, uint32_t ms, uint32_t sampleAt);  // also arms a one-shot stop timer
void motionStop();                          // safe from any task or the stop timer
bool motionActive();
Dir motionDir();
void motionRefreshSafety(uint32_t sampleAt);
bool motionReady();
bool bumperPressed();

const char *motionTakeTrip();
