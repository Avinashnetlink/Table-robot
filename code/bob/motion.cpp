#include "motion.h"
#include "esp_timer.h"
#include "config.h"
static const uint8_t PINS[4] = {PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2};
static SemaphoreHandle_t mutex = nullptr;
static esp_timer_handle_t guard = nullptr;
static control::Lease lease;
static Dir current = Dir::Stop;
static bool ready = false;
static const char *trip = nullptr;
static bool attached[4] = {};
class Lock {
 public: Lock() { xSemaphoreTake(mutex, portMAX_DELAY); }
 ~Lock() { xSemaphoreGive(mutex); }
};
const char *dirName(Dir d) {
  switch (d) {
    case Dir::Forward: return "forward";
    case Dir::PivotLeft: return "pivot_left";
    case Dir::PivotRight: return "pivot_right";
    default: return "stop";
  }
}
bool parseDir(const char *s, Dir &out) {
  if (!s) return false;
  if (!strcmp(s, "forward")) out = Dir::Forward;
  else if (!strcmp(s, "pivot_left")) out = Dir::PivotLeft;
  else if (!strcmp(s, "pivot_right")) out = Dir::PivotRight;
  else if (!strcmp(s, "stop")) out = Dir::Stop;
  else return false;
  return true;
}
bool bumperPressed() { return digitalRead(PIN_BUMPER) == (BUMPER_NC_SERIES ? HIGH : LOW); }
static void stopLocked() {
  for (int i = 0; i < 4; ++i) {
    if (attached[i] && !ledcWrite(PINS[i], 0)) {
      // An unavailable PWM channel must not leave the last duty running.
      ledcDetach(PINS[i]);
      attached[i] = false;
      pinMode(PINS[i], OUTPUT);
      ready = false;
      trip = "PWM stop failed";
    }
    if (!attached[i]) digitalWrite(PINS[i], LOW);
  }
  lease.stop(); current = Dir::Stop;
}
static void guardTick(void *) {
  Lock lock;
  if (lease.active && bumperPressed()) { trip = "bumper"; stopLocked(); }
  else if (lease.expired(millis(), SENSOR_MAX_AGE_MS)) {
    if (control::elapsed(millis(), lease.refreshed, SENSOR_MAX_AGE_MS)) trip = "sensor lease expired";
    stopLocked();
  }
}
bool motionBegin() {
  pinMode(PIN_BUMPER, INPUT);
  for (uint8_t p : PINS) { digitalWrite(p, LOW); pinMode(p, OUTPUT); }
  mutex = xSemaphoreCreateMutex();
  if (!mutex) return false;
  ready = ledcSetClockSource(LEDC_USE_APB_CLK);  // same source as camera XCLK
  for (int i = 0; i < 4; ++i) {
    // Core 3.3.12 allocates timer 0 for these identical outputs; camera uses timer 3/channel 7.
    attached[i] = ledcAttachChannel(PINS[i], PWM_HZ, PWM_BITS, i);
    ready &= attached[i];
  }
  stopLocked();
  esp_timer_create_args_t args = {};
  args.callback = guardTick; args.name = "motor_guard";
  if (esp_timer_create(&args, &guard) != ESP_OK || esp_timer_start_periodic(guard, 5000) != ESP_OK) ready = false;
  return ready;
}
bool motionStart(Dir d, int duty, uint32_t ms, uint32_t sampleAt) {
  if (!mutex || !control::validMove(d, duty, ms, DUTY_CAP_PERCENT, FORWARD_MAX_MS, PIVOT_MAX_MS)) return false;
  Lock lock;
  if (!ready) return false;
  if (control::elapsed(millis(), sampleAt, SENSOR_MAX_AGE_MS) || bumperPressed() || !lease.start(millis(), ms)) return false;
  lease.refreshed = sampleAt;
  current = d;
  uint32_t pwm = uint32_t(duty) * ((1u << PWM_BITS) - 1) / 100;
  uint32_t values[4] = {};
  if (d != Dir::PivotLeft) values[LEFT_MOTOR_REVERSED ? 1 : 0] = pwm;
  if (d != Dir::PivotRight) values[RIGHT_MOTOR_REVERSED ? 3 : 2] = pwm;
  for (int i = 0; i < 4; ++i) {
    if (!ledcWrite(PINS[i], values[i])) { stopLocked(); return false; }
  }
  return true;
}
void motionStop() { if (mutex) { Lock lock; stopLocked(); } }
bool motionActive() { if (!mutex) return false; Lock lock; return lease.active; }
Dir motionDir() { if (!mutex) return Dir::Stop; Lock lock; return current; }
void motionRefreshSafety(uint32_t sampleAt) { if (mutex) { Lock lock; if (lease.active) lease.refreshed = sampleAt; } }
bool motionReady() { if (!mutex) return false; Lock lock; return ready; }

const char *motionTakeTrip() { if (!mutex) return nullptr; Lock lock; const char *result = trip; trip = nullptr; return result; }
