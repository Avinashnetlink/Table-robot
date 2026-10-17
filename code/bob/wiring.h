#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

// Power-on wiring check. Nothing moves: the motor driver stays asleep.

// Call after every part has been started, before the safety task starts.
void wiringCheck(bool pcfOk, bool oledOk, bool adsOk, bool edgeOk, bool audioOk, bool camOk);

int wiringProblems();              // number of FAIL items
const char *wiringFirstProblem();  // part name of the first FAIL, or ""
void wiringPrint();                // table on Serial
void wiringToJson(JsonDocument &doc);
