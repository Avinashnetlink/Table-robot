#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

// Power-on wiring check. Nothing moves: the motor driver stays asleep.

struct MotorPinsAtBoot {
  bool high[4];  // D2, D3, D8, D9 read as inputs before the firmware drives them
};

// Call as the very first line of setup(), before motionBegin().
MotorPinsAtBoot wiringReadMotorPins();

// Call after every part has been started, before the safety task starts.
void wiringCheck(const MotorPinsAtBoot &boot, bool pcfOk, bool oledOk, bool adsOk, bool audioOk, bool camOk);

int wiringProblems();              // number of FAIL items
const char *wiringFirstProblem();  // part name of the first FAIL, or ""
void wiringPrint();                // table on Serial
void wiringToJson(JsonDocument &doc);
