// T09 — Three GP2S700HCP edge sensors through the ADS1115
// Each reading = (LEDs on) - (LEDs off), so room light cancels out.
// Live values are in Serial Plotter format.
//   d  record "desk": hold the sensors about 3 mm over your real desk, press d
//   e  record "edge": hold the sensors past the table edge (over air), press e
//   p  print the result again
// After d and e, the sketch prints EDGE_THRESHOLD_V for code/bob/config.h.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.
// Library: Adafruit ADS1X15.

#include <Wire.h>
#include <Adafruit_ADS1X15.h>

constexpr uint8_t P_LEDS = 1 << 0, P_FAULT = 1 << 3;
constexpr uint32_t SETTLE_MS = 5;  // R10 x C10 = 1 ms, wait 5 time constants
constexpr float SATURATED_V = 3.2f;
const char *NAMES[3] = {"left", "right", "center"};  // A0, A1, A2

Adafruit_ADS1115 ads;
uint8_t PCF_ADDR = 0x20;
float desk[3] = {-1, -1, -1}, edge[3] = {-1, -1, -1};

bool pcfWrite(uint8_t v) {
  Wire.beginTransmission(PCF_ADDR);
  Wire.write(v | P_FAULT | 0xF0);
  return Wire.endTransmission() == 0;
}

void readOnce(float diff[3], float off[3], float on[3]) {
  pcfWrite(0xFF);  // LEDs off
  delay(SETTLE_MS);
  for (int i = 0; i < 3; i++) off[i] = ads.computeVolts(ads.readADC_SingleEnded(i));
  pcfWrite(0xFF & ~P_LEDS);  // LEDs on
  delay(SETTLE_MS);
  for (int i = 0; i < 3; i++) on[i] = ads.computeVolts(ads.readADC_SingleEnded(i));
  pcfWrite(0xFF);
  for (int i = 0; i < 3; i++) diff[i] = on[i] - off[i];
}

void record(float dst[3], const char *label) {
  Serial.printf("# Recording %s for 2 s, hold still...\n", label);
  float sum[3] = {0, 0, 0}, mx[3] = {-9, -9, -9}, mn[3] = {9, 9, 9};
  int n = 0;
  uint32_t end = millis() + 2000;
  while (millis() < end) {
    float d[3], off[3], on[3];
    readOnce(d, off, on);
    for (int i = 0; i < 3; i++) {
      sum[i] += d[i];
      mx[i] = max(mx[i], d[i]);
      mn[i] = min(mn[i], d[i]);
    }
    n++;
  }
  for (int i = 0; i < 3; i++) {
    dst[i] = sum[i] / n;
    Serial.printf("#   %-6s %.3f V (min %.3f, max %.3f)\n", NAMES[i], dst[i], mn[i], mx[i]);
  }
}

void result() {
  if (desk[0] < 0 || edge[0] < 0) {
    Serial.println("# Record both: d (desk) and e (edge).");
    return;
  }
  bool ok = true;
  float th[3];
  Serial.println("# Result:");
  for (int i = 0; i < 3; i++) {
    float gap = desk[i] - edge[i];
    th[i] = edge[i] + gap / 2;
    bool good = gap > 0.15f;
    ok &= good;
    Serial.printf("#   %-6s desk %.3f  edge %.3f  gap %.3f  -> %s\n", NAMES[i], desk[i], edge[i], gap,
                  good ? "OK" : "TOO SMALL: lower the sensor, add a shade, or check wiring");
  }
  Serial.println("# Copy into code/bob/config.h:");
  Serial.printf("  constexpr float EDGE_THRESHOLD_V[3] = {%.3f, %.3f, %.3f};  // left, right, center\n",
                th[0], th[1], th[2]);
  Serial.println(ok ? "# PASS (now repeat over white paper and dark material; every desk reading must stay above its threshold)"
                    : "# FAIL - fix the sensor that is too small, then record again");
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T09 edge sensors ===");
  Wire.begin();
  Wire.setClock(400000);
  if (!pcfWrite(0xFF)) {
    PCF_ADDR = 0x38;
    if (!pcfWrite(0xFF)) Serial.println("FAIL: no PCF8574 - the LEDs cannot be switched. Run T07.");
  }
  if (!ads.begin(0x48)) {
    Serial.println("FAIL: no ADS1115 at 0x48. Run T03.");
    while (true) delay(1000);
  }
  ads.setGain(GAIN_ONE);
  ads.setDataRate(RATE_ADS1115_860SPS);
  Serial.println("# Keys: d desk, e edge, p print. Plotter shows LEDs-on minus LEDs-off per sensor.");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'd') { record(desk, "DESK"); result(); }
    if (c == 'e') { record(edge, "EDGE / AIR"); result(); }
    if (c == 'p') result();
  }

  float d[3], off[3], on[3];
  readOnce(d, off, on);
  Serial.printf("left:%.3f right:%.3f center:%.3f\n", d[0], d[1], d[2]);
  for (int i = 0; i < 3; i++) {
    if (on[i] > SATURATED_V) Serial.printf("# %s saturated - raise R%d (10k) to a lower value or lift the sensor\n", NAMES[i], 10 + i);
    if (off[i] > 1.0f) Serial.printf("# %s sees strong room light with LEDs off - add a shade\n", NAMES[i]);
  }
  delay(50);
}
