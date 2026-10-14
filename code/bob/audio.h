#pragma once
#include <Arduino.h>

bool audioBegin();  // microphone first (it needs I2S0), then the speaker
void audioEnd();    // amp off, both I2S ports stopped

// Microphone: returns the number of samples read (blocks for one chunk).
size_t micRead(int16_t *samples, size_t count);
bool micAllowed();  // false while speaking and for a short time after

// Speaker: PCM 16 kHz 16-bit mono. The amp turns on with the first chunk
// and off after SPEAKER_IDLE_MS without data, or at speakerEnd().
void speakerPlay(const uint8_t *pcm, size_t len);
void speakerEnd();
void audioService();
bool speaking();
