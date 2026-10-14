#pragma once
#include <Arduino.h>

struct EdgeReading {
  float diff[3];   // LEDs on minus LEDs off, volts: left, right, center
  bool table[3];   // true = table under that sensor
  bool ok;         // false = I2C error, saturated, or too much room light
  const char *problem;
};

bool sensorsBegin();
bool sensorsReadEdges(EdgeReading &out);  // about 20 ms, turns the LEDs on then off
bool sensorsReadBattery(float &volts);    // calibrated cell voltage
