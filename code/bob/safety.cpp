#include "safety.h"
#include "esp_task_wdt.h"
#include "config.h"
#include "pcf.h"
#include "sensors.h"

struct MoveRequest { Dir dir; int duty; uint32_t ms, queued; };
static SemaphoreHandle_t stateMutex = nullptr, sleepAck = nullptr;
static QueueHandle_t requests = nullptr, events = nullptr;
static SafetySnapshot snap = {};
static bool suspended = false, patrol = false, unlocked = false, speaker = false;
static bool bootHealthy = false, linkSeen = false, sleepRequested = false;
static uint32_t heartbeatAt = 0;
static const char *lastStop = "boot";
class StateLock {
 public: StateLock() { if (stateMutex) xSemaphoreTake(stateMutex, portMAX_DELAY); }
 ~StateLock() { if (stateMutex) xSemaphoreGive(stateMutex); }
};
static void event(const char *what, const char *detail, bool ok) {
  SafetyEvent e{what, detail, ok};
  if (events) xQueueSend(events, &e, 0);
}
static void stopLocked(const char *why) {
  motionStop(); patrol = false; unlocked = false;
  if (requests) xQueueReset(requests);
  lastStop = why;
  event("stopped", why, false);
}
static control::Inputs inputs(const SafetySnapshot &s, uint32_t now) {
  control::Inputs g;
  g.calibrated = CALIBRATION_CONFIRMED && bootHealthy && motionReady() && !sleepRequested;
  g.unlocked = unlocked;
  g.link = linkSeen && !control::elapsed(now, heartbeatAt, LINK_LEASE_MS);
  g.speaking = speaker;
  g.batteryValid = s.batteryValid && !control::elapsed(now, s.batteryAt, BATTERY_MAX_AGE_MS);
  g.batteryOk = s.batteryOk;
  g.sensorsOk = s.sensorsOk && !control::elapsed(now, s.sampleAt, SENSOR_MAX_AGE_MS);
  for (int i = 0; i < 3; ++i) g.table[i] = s.table[i];
  g.bumper = s.bumper || bumperPressed(); g.fault = s.fault;
  return g;
}
static bool startLocked(const SafetySnapshot &s, const MoveRequest &r) {
  const char *why = control::inhibit(inputs(s, millis()));
  if (!why && !control::validMove(r.dir, r.duty, r.ms, DUTY_CAP_PERCENT, FORWARD_MAX_MS, PIVOT_MAX_MS)) why = "invalid move limits";
  if (!why && motionActive()) why = "already moving";
  if (!why && control::elapsed(millis(), r.queued, REQUEST_MAX_AGE_MS)) why = "request expired";
  if (!why) {
    if (!pcfSet(PCF_DRIVER, true)) why = "driver enable failed";
    else {
      vTaskDelay(pdMS_TO_TICKS(2));
      why = control::inhibit(inputs(s, millis()));
      if (!why && pcfFaultActive()) why = "driver fault";
      if (!why && !motionStart(r.dir, r.duty, r.ms, s.sampleAt)) why = "motor start failed";
    }
  }
  if (why) { motionStop(); pcfSet(PCF_DRIVER, false); }
  event("move_result", why ? why : dirName(r.dir), !why);
  return !why;
}
static void safetyTask(void *) {
  if (esp_task_wdt_add(nullptr) != ESP_OK) { StateLock lock; bootHealthy = false; }
  uint32_t cycles = 0, lowSince = 0, pausedAt = 0;
  bool lowTiming = false, warned = false, wasMoving = false;
  for (;;) {
    esp_task_wdt_reset();
    bool pause;
    { StateLock lock; pause = suspended; }
    if (pause) {
      motionStop(); pcfReleaseAll();
      xSemaphoreGive(sleepAck);
      esp_task_wdt_delete(nullptr);
      vTaskSuspend(nullptr);
    }
    uint32_t began = millis();
    if (bumperPressed()) { StateLock lock; if (unlocked || patrol || motionActive()) stopLocked("bumper"); }
    EdgeReading er;
    sensorsReadEdges(er);
    SafetySnapshot s = {};
    s.sampleAt = er.sampleAt;  // cached range data must never receive a newer lease
    s.sensorsOk = er.ok;
    for (int i = 0; i < 3; ++i) { s.table[i] = er.table[i]; s.edgeMm[i] = er.mm[i]; s.edgeValid[i] = er.valid[i]; s.edgeStatus[i] = er.status[i]; }
    s.batteryValid = sensorsReadBattery(s.battery);  // every cycle, including under motor load
    s.batteryAt = millis();
    s.batteryOk = s.batteryValid && s.battery >= BATTERY_LOCK_V;
    s.batteryWarn = s.batteryValid && s.battery < BATTERY_WARN_V;
    s.bumper = bumperPressed(); s.fault = pcfFaultActive();
    uint32_t now = millis();
    s.cycleMs = now - began; s.cycles = ++cycles;
    {
      StateLock lock;
      if (suspended) continue;
      const char *trip = motionTakeTrip();
      const char *why = control::inhibit(inputs(s, now));
      if (trip) stopLocked(trip);
      else if (why && (unlocked || patrol || motionActive())) stopLocked(why);
      else if (!why) motionRefreshSafety(s.sampleAt);
      bool moving = motionActive();
      if (wasMoving && !moving) pausedAt = now;
      if (!moving) pcfSet(PCF_DRIVER, false);
      if (s.batteryWarn && !warned) { event("battery", "low", false); warned = true; }
      if (s.batteryValid && s.battery > BATTERY_WARN_V + 0.05f) warned = false;
      if (s.batteryValid && s.battery < BATTERY_SLEEP_V) {
        if (!lowTiming) { lowSince = now; lowTiming = true; }
        if (!sleepRequested && control::elapsed(now, lowSince, BATTERY_SLEEP_MS)) { sleepRequested = true; stopLocked("battery empty"); }
      } else lowTiming = false;
      MoveRequest r;
      if (xQueueReceive(requests, &r, 0) == pdTRUE) {
        if (patrol) event("move_result", "patrol running", false);
        else if (!startLocked(s, r)) stopLocked("move refused");
      }
      if (patrol && !motionActive() && control::elapsed(now, pausedAt, PATROL_PAUSE_MS)) {
        // Without rear/side coverage, never pivot to escape a detected cliff.
        r = {Dir::Forward, PATROL_DUTY_PERCENT, PATROL_FORWARD_MS, now};
        if (!startLocked(s, r)) stopLocked("patrol refused");
      }
      s.moving = motionActive(); s.dir = motionDir(); wasMoving = s.moving;
      s.patrol = patrol; s.unlocked = unlocked; s.speaking = speaker;
      s.linkOk = linkSeen && !control::elapsed(now, heartbeatAt, LINK_LEASE_MS);
      s.sleepRequested = sleepRequested;
      s.calibrated = CALIBRATION_CONFIRMED; s.stopReason = lastStop;
      s.maxCycleMs = max(s.cycleMs, snap.maxCycleMs);
      snap = s;
    }
    vTaskDelay(pdMS_TO_TICKS(5));
  }
}
bool safetyBegin(bool healthy) {
  stateMutex = xSemaphoreCreateMutex(); sleepAck = xSemaphoreCreateBinary();
  requests = xQueueCreate(1, sizeof(MoveRequest)); events = xQueueCreate(16, sizeof(SafetyEvent));
  bootHealthy = healthy;
  if (!stateMutex || !sleepAck || !requests || !events) return false;
  return xTaskCreatePinnedToCore(safetyTask, "safety", 6144, nullptr, 3, nullptr, 1) == pdPASS;
}
bool safetySuspend() {
  { StateLock lock; suspended = true; stopLocked("sleep"); }
  return sleepAck && xSemaphoreTake(sleepAck, pdMS_TO_TICKS(500)) == pdTRUE;
}
SafetySnapshot safetyGet() {
  StateLock lock;
  SafetySnapshot s = snap;
  s.moving = motionActive(); s.dir = motionDir();
  s.unlocked = unlocked; s.patrol = patrol; s.speaking = speaker;
  s.stopReason = lastStop; s.sleepRequested = sleepRequested;
  s.linkOk = linkSeen && !control::elapsed(millis(), heartbeatAt, LINK_LEASE_MS);
  return s;
}
bool safetyPopEvent(SafetyEvent &e) { return events && xQueueReceive(events, &e, 0) == pdTRUE; }
bool safetyRequestMove(Dir d, int duty, uint32_t ms) {
  if (d == Dir::Stop) { safetyStopAll("move stop"); return true; }
  StateLock lock;
  if (!requests || suspended || !unlocked || patrol || motionActive()) return false;
  MoveRequest r{d, duty, ms, millis()};
  return xQueueSend(requests, &r, 0) == pdTRUE;
}
void safetyStopAll(const char *why) { StateLock lock; stopLocked(why); }
void safetySetPatrol(bool on) {
  StateLock lock;
  if (!on) { stopLocked("patrol off"); return; }
  if (!unlocked || suspended) { event("patrol", "locked", false); return; }
  patrol = true; event("patrol", "on", true);
}
void safetySetUnlocked(bool on) {
  StateLock lock;
  if (!on) { stopLocked("locked"); return; }
  if (!stateMutex || suspended) return;
  auto g = inputs(snap, millis()); g.unlocked = true;
  const char *why = control::inhibit(g);
  if (why) { event("unlock", why, false); return; }
  unlocked = true; event("unlock", "touch", true);
}
void safetySetSpeaking(bool on) {
  StateLock lock;
  speaker = on;
  if (on) stopLocked("speech");
}
void safetyHeartbeat() { StateLock lock; heartbeatAt = millis(); linkSeen = true; }
