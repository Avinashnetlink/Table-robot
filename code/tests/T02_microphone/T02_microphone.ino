#include <Wire.h>
// T02 — Built-in PDM microphone
// Prints the sound level 20 times a second. Open Tools > Serial Plotter and clap.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.

#include <ESP_I2S.h>

constexpr int MIC_CLK = 42;   // D11 on the Sense board
constexpr int MIC_DATA = 41;  // D12 on the Sense board
constexpr int SAMPLE_RATE = 16000;
constexpr int BLOCK = SAMPLE_RATE / 20;  // 50 ms

I2SClass mic;
int16_t samples[BLOCK];
uint32_t blocks = 0;
int32_t loudestPeak = 0;


// Reset the retained expander latch BEFORE any startup delay.
static void benchSafeBoot() {
  for (int p : {D2, D3, D8, D9}) { digitalWrite(p, LOW); pinMode(p, OUTPUT); }
  Wire.begin(D4, D5, 100000); Wire.setTimeOut(10);
  for (uint8_t a : {0x20, 0x38}) {
    Wire.beginTransmission(a); Wire.write(0xFF); Wire.endTransmission();
  }
}

void setup() {
  benchSafeBoot();
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T02 microphone ===");

  mic.setPinsPdmRx(MIC_CLK, MIC_DATA);
  if (!mic.begin(I2S_MODE_PDM_RX, SAMPLE_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO)) {
    Serial.println("FAIL: microphone did not start. Is this the Sense board, with the mic jumpers intact?");
    while (true) delay(1000);
  }
  Serial.println("Clap near the board. 'level' should jump far above the quiet value.");
}

void loop() {
  size_t got = mic.readBytes((char *)samples, sizeof(samples)) / sizeof(int16_t);
  if (got == 0) return;

  int64_t sum = 0;
  for (size_t i = 0; i < got; i++) sum += samples[i];
  int32_t mean = sum / (int32_t)got;  // remove the DC offset

  uint64_t sq = 0;
  int32_t peak = 0;
  for (size_t i = 0; i < got; i++) {
    int32_t v = samples[i] - mean;
    sq += (int64_t)v * v;
    if (abs(v) > peak) peak = abs(v);
  }
  int32_t rms = sqrt((double)sq / got);
  if (peak > loudestPeak) loudestPeak = peak;

  // Serial Plotter format
  Serial.printf("level:%d peak:%d\n", int(rms), int(peak));

  if (++blocks % 100 == 0) {
    Serial.printf("# loudest peak in the last 5 s: %d (%s)\n", int(loudestPeak),
                  loudestPeak > 3000 ? "PASS, the mic hears you" : "quiet - clap closer");
    loudestPeak = 0;
  }
}
