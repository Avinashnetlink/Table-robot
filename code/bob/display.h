#pragma once
#include <Arduino.h>

bool displayBegin();
void displaySetText(const char *line1, const char *line2, uint32_t holdMs = 8000);
void displaySetMood(const char *state);  // "awake", "listening", "thinking", "speaking", "moving", "offline"
void displayUpdate(float battery, bool batteryWarn, bool wifi, bool unlocked, bool patrol);
void displayOff();
