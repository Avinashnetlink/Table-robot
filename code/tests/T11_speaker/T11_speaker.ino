// T11 — MAX98357A amplifier and speaker
// Turns the amp on through the Q1 safe switch (PCF P1), plays a quiet tone and a
// chime, then turns the amp off again.
//   t  tone 440 Hz 1 s     c  chime     +  louder     -  quieter
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.

#include <Wire.h>
#include <ESP_I2S.h>

constexpr uint8_t PIN_BCLK = D6, PIN_LRC = D7, PIN_DIN = D10;
constexpr uint8_t P_AMP = 1 << 1, P_FAULT = 1 << 3;
constexpr int RATE = 16000;

I2SClass speaker;
uint8_t PCF_ADDR = 0x20;
float volume = 0.10f;  // fraction of full scale; start quiet

bool pcfWrite(uint8_t v) {
  Wire.beginTransmission(PCF_ADDR);
  Wire.write(v | P_FAULT | 0xF0);
  return Wire.endTransmission() == 0;
}

void ampOn(bool on) {
  pcfWrite(on ? (0xFF & ~P_AMP) : 0xFF);
  if (on) delay(10);  // MAX98357A start-up time is a few ms
}

void playTone(float hz, uint32_t ms) {
  const int block = 256;
  int16_t buf[block];
  uint32_t total = (uint32_t)RATE * ms / 1000;
  float phase = 0, step = 2 * PI * hz / RATE;
  for (uint32_t done = 0; done < total; done += block) {
    for (int i = 0; i < block; i++) {
      // short fade in and out avoids clicks
      uint32_t k = done + i;
      float env = min(1.0f, min(k, total - min(k, total)) / (RATE * 0.01f));
      buf[i] = (int16_t)(sinf(phase) * env * volume * 32767);
      phase += step;
      if (phase > 2 * PI) phase -= 2 * PI;
    }
    speaker.write((uint8_t *)buf, sizeof(buf));
  }
}

void silence(uint32_t ms) {
  int16_t zero[256] = {0};
  for (uint32_t s = 0; s < (uint32_t)RATE * ms / 1000; s += 256) speaker.write((uint8_t *)zero, sizeof(zero));
}

void tone() {
  Serial.printf("Tone 440 Hz at volume %.0f%%\n", volume * 100);
  ampOn(true);
  playTone(440, 1000);
  silence(50);
  ampOn(false);
}

void chime() {
  Serial.println("Chime");
  ampOn(true);
  playTone(660, 150);
  playTone(880, 150);
  playTone(1320, 300);
  silence(50);
  ampOn(false);
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T11 speaker ===");
  Wire.begin();
  if (!pcfWrite(0xFF)) {
    PCF_ADDR = 0x38;
    if (!pcfWrite(0xFF)) Serial.println("WARNING: no PCF8574 - the amp stays shut down (SD low). Run T07.");
  }

  speaker.setPins(PIN_BCLK, PIN_LRC, PIN_DIN);
  if (!speaker.begin(I2S_MODE_STD, RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO)) {
    Serial.println("FAIL: I2S did not start.");
    while (true) delay(1000);
  }
  Serial.println("Keys: t tone, c chime, + louder, - quieter. Speaker wires only on OUT+ and OUT-.");
  tone();
}

void loop() {
  if (!Serial.available()) return;
  switch (Serial.read()) {
    case 't': tone(); break;
    case 'c': chime(); break;
    case '+': volume = min(0.5f, volume + 0.05f); Serial.printf("Volume %.0f%%\n", volume * 100); break;
    case '-': volume = max(0.02f, volume - 0.05f); Serial.printf("Volume %.0f%%\n", volume * 100); break;
  }
}
