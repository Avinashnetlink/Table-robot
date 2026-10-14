// Connections: D2 -> DRV8833 AIN1, D3 -> AIN2 (left motor), D8 -> BIN1, D9 -> BIN2 (right motor).
// Each input has a 100k pulldown (R3-R6). The driver's SLP comes from Q2 (PCF P2), see safety.cpp.
#include "motion.h"
#include "esp_timer.h"
#include "config.h"

static const uint8_t PINS[4] = {PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2};
static esp_timer_handle_t stopTimer = nullptr;
static volatile bool active = false;
static volatile Dir current = Dir::Stop;

const char *dirName(Dir d) {
  switch (d) {
    case Dir::Forward: return "forward";
    case Dir::PivotLeft: return "pivot_left";
    case Dir::PivotRight: return "pivot_right";
    default: return "stop";
  }
}

bool parseDir(const char *s, Dir &out) {
  if (!strcmp(s, "forward")) out = Dir::Forward;
  else if (!strcmp(s, "pivot_left")) out = Dir::PivotLeft;
  else if (!strcmp(s, "pivot_right")) out = Dir::PivotRight;
  else if (!strcmp(s, "stop")) out = Dir::Stop;
  else return false;  // "reverse" and anything else are refused
  return true;
}

static void writeDuty(uint8_t i, int percent) {
  ledcWrite(PINS[i], (uint32_t)percent * ((1u << PWM_BITS) - 1) / 100);
}

static void allLow() {
  for (uint8_t i = 0; i < 4; i++) writeDuty(i, 0);
}

static void onStopTimer(void *) { motionStop(); }

void motionBegin() {
  for (uint8_t i = 0; i < 4; i++) {
    pinMode(PINS[i], OUTPUT);
    digitalWrite(PINS[i], LOW);
    // Channels 0-3 use LEDC timers 0 and 1; the camera clock uses timer 3.
    ledcAttachChannel(PINS[i], PWM_HZ, PWM_BITS, i);
    ledcWrite(PINS[i], 0);
  }
  esp_timer_create_args_t args = {};
  args.callback = onStopTimer;
  args.name = "motor_stop";
  esp_timer_create(&args, &stopTimer);
}

bool motionStart(Dir d, int dutyPercent, uint32_t ms) {
  motionStop();
  if (d == Dir::Stop || ms == 0 || dutyPercent <= 0) return false;
  dutyPercent = constrain(dutyPercent, 0, 100);

  // Fast decay: one input PWM, the other low. Left = A, right = B.
  int left = 0, right = 0;
  if (d == Dir::Forward) left = right = dutyPercent;
  if (d == Dir::PivotLeft) right = dutyPercent;
  if (d == Dir::PivotRight) left = dutyPercent;

  current = d;
  active = true;
  esp_timer_start_once(stopTimer, (uint64_t)ms * 1000);
  writeDuty(0, left);
  writeDuty(1, 0);
  writeDuty(2, right);
  writeDuty(3, 0);
  return true;
}

void motionStop() {
  allLow();
  if (stopTimer) esp_timer_stop(stopTimer);
  active = false;
  current = Dir::Stop;
}

bool motionActive() { return active; }
Dir motionDir() { return current; }
