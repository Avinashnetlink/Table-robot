// Connections: microphone on the Sense board, clock GPIO42, data GPIO41.
// MAX98357A: BCLK D6, LRC D7, DIN D10, SD from Q1 (PCF P1), VIN from VBAT (C5, C6), GAIN R22 to VIN.
#include "audio.h"
#include <ESP_I2S.h>
#include "config.h"
#include "pcf.h"
#include "safety.h"

static I2SClass mic;
static I2SClass spk;
static bool micOk = false, spkOk = false;
static bool isSpeaking = false;
static uint32_t lastChunk = 0, speakEndedAt = 0;

bool audioBegin() {
  // PDM receive only exists on I2S0, so the microphone must claim it first.
  mic.setPinsPdmRx(PIN_MIC_CLK, PIN_MIC_DATA);
  micOk = mic.begin(I2S_MODE_PDM_RX, AUDIO_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO);
  mic.setTimeout(100);

  spk.setPins(PIN_I2S_BCLK, PIN_I2S_LRC, PIN_I2S_DOUT);
  spkOk = spk.begin(I2S_MODE_STD, AUDIO_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO);
  return micOk && spkOk;
}

void audioEnd() {
  speakerEnd();
  if (micOk) mic.end();
  if (spkOk) spk.end();
  micOk = spkOk = false;
}

size_t micRead(int16_t *samples, size_t count) {
  if (!micOk) return 0;
  return mic.readBytes((char *)samples, count * sizeof(int16_t)) / sizeof(int16_t);
}

bool micAllowed() { return micOk && !isSpeaking && millis() - speakEndedAt > MIC_AFTER_SPEAK_MS; }

void speakerPlay(const uint8_t *pcm, size_t len) {
  if (!spkOk) return;
  if (!isSpeaking) {
    isSpeaking = true;
    safetySetSpeaking(true);
    pcfSet(PCF_AMP, true);
    delay(10);  // amp start-up
  }
  lastChunk = millis();
  spk.write((uint8_t *)pcm, len);
}

void speakerEnd() {
  if (!isSpeaking) return;
  static const int16_t zeros[256] = {0};
  if (spkOk) spk.write((uint8_t *)zeros, sizeof(zeros));  // flush with silence, no click
  pcfSet(PCF_AMP, false);
  isSpeaking = false;
  speakEndedAt = millis();
  safetySetSpeaking(false);
}

void audioService() {
  if (isSpeaking && millis() - lastChunk > SPEAKER_IDLE_MS) speakerEnd();
}

bool speaking() { return isSpeaking; }
