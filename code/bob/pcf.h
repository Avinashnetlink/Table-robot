#pragma once
#include <Arduino.h>

// PCF8574 at PCF_ADDR. Writing a bit 0 turns that part on.
bool pcfBegin();                 // releases every pin (0xFF)
bool pcfSet(uint8_t bit, bool on);
bool pcfReleaseAll();
bool pcfFaultActive();           // true on driver fault or if the expander cannot be read
bool pcfIsOn(uint8_t bit);
