#pragma once
#include <Arduino.h>
struct EdgeReading {
  uint16_t mm[3];
  uint8_t status[3]; // native range status; 250=I2C/mux fault, 251=stale/not ready
  bool valid[3], table[3];
  bool ok;
  uint32_t sampleAt; // oldest acquisition start/previous interrupt-clear timestamp
  const char *problem;
};
bool sensorsBegin(); // battery ADC only
bool sensorsReadBattery(float &volts);
bool edgesBegin(); // required three ToF sensors and multiplexer
bool sensorsReadEdges(EdgeReading &out); // polls without waiting for conversion
void edgesEnd();
const char *edgeSensorName();
