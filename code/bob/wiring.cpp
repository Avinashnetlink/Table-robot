#include "wiring.h"
#include "audio.h"
#include "camera.h"
#include "config.h"
#include "motion.h"
#include "pcf.h"
#include "secrets.h"
#include "sensors.h"

enum class Result : uint8_t { Ok, Warn, Fail };

struct Item {
  const char *part;
  Result result;
  char detail[64];
};

static Item items[16];
static int count = 0;

static void add(const char *part, Result r, const char *fmt, ...) {
  if (count >= (int)(sizeof(items) / sizeof(items[0]))) return;
  Item &it = items[count++];
  it.part = part;
  it.result = r;
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(it.detail, sizeof(it.detail), fmt, ap);
  va_end(ap);
}

static const char *resultName(Result r) { return r == Result::Ok ? "OK" : r == Result::Warn ? "CHECK" : "FAIL"; }

void wiringCheck(bool pcfOk, bool oledOk, bool adsOk, bool edgeOk, bool audioOk, bool camOk) {
  count = 0;

  // ---- I2C parts on D4 (SDA) / D5 (SCL) ----
  add("PCF8574 expander", pcfOk ? Result::Ok : Result::Fail,
      pcfOk ? "answers at 0x%02X" : "no answer at 0x%02X - run T03", PCF_ADDR);
  add("OLED screen", oledOk ? Result::Ok : Result::Fail,
      oledOk ? "answers at 0x%02X" : "no answer at 0x%02X - run T03", OLED_ADDR);
  add("ADS1115 ADC", adsOk ? Result::Ok : Result::Fail,
      adsOk ? "answers at 0x%02X" : "no answer at 0x%02X - ADDR to GND", ADS_ADDR);

  // ---- Battery divider R1 / R2 / C9 on ADS1115 A3 ----
  if (adsOk) {
    float v = 0;
    bool ok = sensorsReadBattery(v);
    if (!ok) add("Battery divider A3", Result::Fail, "invalid ADC/battery reading: check power and divider");
    else if (v >= 3.0f && v <= 4.35f) add("Battery divider A3", Result::Ok, "%.2f V", v);
    else add("Battery divider A3", Result::Warn, "%.2f V is odd: check R1 = R2 = 100k", v);
  }

  // ---- DRV8833 FLT on PCF P3 (driver asleep, so it must read high) ----
  if (pcfOk) {
    bool fault = pcfFaultActive();
    add("Driver FLT -> P3", fault ? Result::Fail : Result::Ok,
        fault ? "reads low: FLT shorted to GND or R21 wrong" : "high (no fault)");
  }

  add("Motor pulldowns/J3", Result::Warn, "must verify with power off; GPIO reads cannot prove wiring");
  // ---- Bumper on D1 with R14 pull-up ----
  pinMode(PIN_BUMPER, INPUT);
  bool bumperLow = bumperPressed();
  add("Bumper D1", bumperLow ? Result::Fail : Result::Ok,
      bumperLow ? "pressed/unsafe: check contacts and configured polarity" : "released per configured polarity");

  add("ToF edges / TCA9548A", edgeOk ? Result::Ok : Result::Fail,
      edgeOk ? "%s: three initialized; run T09" : "%s: missing/wrong module or mux; run T09", edgeSensorName());

  // ---- Touch pad on D0 through R13 ----
  uint32_t t = touchRead(PIN_TOUCH);
  bool touchNear = t > TOUCH_IDLE / 2 && t < TOUCH_IDLE * 2;
  add("Touch pad D0", touchNear ? Result::Ok : Result::Warn,
      touchNear ? "%lu (calibrated %lu)" : "%lu vs calibrated %lu: run T05", (unsigned long)t,
      (unsigned long)TOUCH_IDLE);

  // ---- Microphone GPIO42 / GPIO41 ----
  if (audioOk) {
    static int16_t s[1600];  // 100 ms
    size_t n = micRead(s, 1600);
    int16_t lo = 32767, hi = -32768;
    for (size_t i = 0; i < n; i++) {
      lo = min(lo, s[i]);
      hi = max(hi, s[i]);
    }
    bool alive = n > 0 && hi - lo > 4;
    add("Microphone", alive ? Result::Ok : Result::Fail, alive ? "signal %d" : "silent: check mic jumpers",
        hi - lo);

    // ---- Speaker: MAX98357A on D6 / D7 / D10, SD through Q1 (P1) ----
    add("Speaker", Result::Warn, "I2S initialized; audible output requires T11");
  } else {
    add("Audio I2S", Result::Fail, "I2S did not start");
  }

  // ---- Camera ribbon ----
  add("Camera", camOk ? Result::Ok : Result::Fail, camOk ? "%s" : "not detected: reseat the ribbon",
      cameraName());

  // ---- Settings ----
  bool wifiSet = strcmp(WIFI_SSID, "your-wifi") != 0;
  add("Wi-Fi settings", wifiSet ? Result::Ok : Result::Fail, wifiSet ? "%s" : "edit secrets.h", WIFI_SSID);
  bool calibrated = CALIBRATION_CONFIRMED;
  add("Calibration", calibrated ? Result::Ok : Result::Warn,
      calibrated ? "config.h has test values" : "config.h has defaults: run T05, T06, T09");
}

int wiringProblems() {
  int n = 0;
  for (int i = 0; i < count; i++) n += items[i].result == Result::Fail;
  return n;
}

const char *wiringFirstProblem() {
  for (int i = 0; i < count; i++)
    if (items[i].result == Result::Fail) return items[i].part;
  return "";
}

void wiringPrint() {
  Serial.println("\nWiring check");
  for (int i = 0; i < count; i++)
    Serial.printf("  %-20s %-5s %s\n", items[i].part, resultName(items[i].result), items[i].detail);
  int n = wiringProblems();
  if (n) Serial.printf("%d problem(s). Fix every FAIL line before driving.\n\n", n);
  else Serial.println("No software-detected failures; physical checks still required.\n");
}

void wiringToJson(JsonDocument &doc) {
  doc["type"] = "wiring";
  doc["problems"] = wiringProblems();
  JsonArray arr = doc["items"].to<JsonArray>();
  for (int i = 0; i < count; i++) {
    JsonObject o = arr.add<JsonObject>();
    o["part"] = items[i].part;
    o["result"] = resultName(items[i].result);
    o["detail"] = items[i].detail;
  }
}
