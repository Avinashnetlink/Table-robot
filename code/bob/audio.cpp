// Connections: microphone on the Sense board, clock GPIO42, data GPIO41.
// MAX98357A: BCLK D6, LRC D7, DIN D10, SD from Q1 (PCF P1), VIN from VBAT (C5, C6), GAIN R22 to VIN.
#include "audio.h"
#include <ESP_I2S.h>
#include "config.h"
#include "pcf.h"
#include "safety.h"

static I2SClass mic(I2S_NUM_0);
static I2SClass spk(I2S_NUM_1);
static bool micOk = false, spkOk = false;
static bool isSpeaking = false;
static uint32_t lastChunk = 0, speakEndedAt = 0;

bool audioBegin() {
  // PDM receive only exists on I2S0, so the microphone must claim it first.
  mic.setPinsPdmRx(PIN_MIC_CLK, PIN_MIC_DATA);
  micOk = mic.begin(I2S_MODE_PDM_RX, AUDIO_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO);
  mic.setTimeout(60);

  spk.setPins(PIN_I2S_BCLK, PIN_I2S_LRC, PIN_I2S_DOUT);
  spkOk = spk.begin(I2S_MODE_STD, AUDIO_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO);
  spk.setTimeout(160);
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
  if (!spkOk || !pcm || !len || len > MAX_PLAY_BYTES || len % 2) return;
  if (!isSpeaking) {
    isSpeaking = true;
    safetySetSpeaking(true);
    if (!pcfSet(PCF_AMP, true)) { speakerEnd(); return; }
    delay(10);  // amp start-up
  }
  lastChunk = millis();
  // Bound output amplitude on the robot too; laptop volume alone is not a limit.
  static int16_t limited[MAX_PLAY_BYTES / 2];
  for (size_t i = 0; i < len / 2; ++i) {
    int16_t sample = int16_t(uint16_t(pcm[2*i]) | (uint16_t(pcm[2*i+1]) << 8));
    limited[i] = constrain(sample, -12000, 12000);
  }
  if (spk.write(reinterpret_cast<uint8_t *>(limited), len) != len) speakerEnd();
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
  // Drain queued microphone DMA audio during playback and the echo tail.
  if (micOk && !micAllowed()) {
    int16_t discard[256];
    size_t bytes = 0;
    for (int i = 0; i < 8; ++i) {
      if (i2s_channel_read(mic.rxChan(), discard, sizeof(discard), &bytes, 0) != ESP_OK || !bytes) break;
    }
  }
  if (isSpeaking && millis() - lastChunk > SPEAKER_IDLE_MS) speakerEnd();
}

bool speaking() { return isSpeaking; }
