// Connections: bumper on D1 (R14 10k pull-up, C14), edge sensors and battery through sensors.cpp,
// driver SLP (PCF P2 via Q2) and FLT (PCF P3) through pcf.cpp, motor inputs through motion.cpp.
#include "safety.h"
#include "esp_task_wdt.h"
#include "config.h"
#include "pcf.h"
#include "sensors.h"

struct MoveRequest {
  Dir dir;
  int duty;
  uint32_t ms;
};

static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
static SafetySnapshot snap = {};
static QueueHandle_t requests = nullptr;
static QueueHandle_t events = nullptr;
static volatile bool suspended = false;
static volatile bool patrolOn = false, unlockedFlag = false, speakingFlag = false;

static void pushEvent(const char *what, const char *detail, bool ok) {
  SafetyEvent e = {what, detail, ok};
  xQueueSend(events, &e, 0);  // drop if the loop is behind; the status message still shows the state
}

// Which sensors must see the table for a move in this direction.
// A pivot turns toward the side that still sees the table, so it needs the
// center sensor and the sensor on the turning side.
static bool tableOkFor(Dir d, const bool t[3]) {
  const bool left = t[0], right = t[1], center = t[2];
  switch (d) {
    case Dir::Forward: return left && right && center;
    case Dir::PivotLeft: return center && left;
    case Dir::PivotRight: return center && right;
    default: return false;
  }
}

// Ends motion and patrol, and locks motion until the next 2-second touch.
static void hardStop(const char *what, const char *why) {
  motionStop();
  if (patrolOn) pushEvent("patrol", "off", false);
  patrolOn = false;
  unlockedFlag = false;
  pushEvent(what, why, false);
}

static const char *checkStart(const SafetySnapshot &s, Dir d, int duty, uint32_t ms) {
  if (!unlockedFlag) return "locked: hold the touch pad 2 s";
  if (speakingFlag) return "speaking";
  if (!s.batteryValid || !s.batteryOk) return "battery low";
  if (!s.sensorsOk) return "sensor problem";
  if (s.bumper) return "bumper pressed";
  if (s.fault) return "driver fault";
  if (d == Dir::Stop) return "no direction";
  if (duty <= 0 || duty > DUTY_CAP_PERCENT) return "duty over the cap";
  uint32_t maxMs = d == Dir::Forward ? FORWARD_MAX_MS : PIVOT_MAX_MS;
  if (ms == 0 || ms > maxMs) return "too long";
  if (!tableOkFor(d, s.table)) return "no table under the sensors";
  return nullptr;
}

static bool startMove(const SafetySnapshot &s, Dir d, int duty, uint32_t ms) {
  if (!pcfSet(PCF_DRIVER, true)) return false;
  vTaskDelay(pdMS_TO_TICKS(2));  // DRV8833 wake-up time is 1 ms
  return motionStart(d, duty, ms);
}

static void safetyTask(void *) {
  esp_task_wdt_add(nullptr);
  uint32_t lastBattery = 0, lowSince = 0, lastStepEnd = 0, cyclesAtStop = 0;
  bool wasMoving = false, lastBumper = false, warned = false;
  float battery = 0;
  bool batteryValid = false;

  for (;;) {
    esp_task_wdt_reset();
    if (suspended) {
      motionStop();
      vTaskDelay(pdMS_TO_TICKS(50));
      continue;
    }
    uint32_t now = millis();

    // Fast check before the slower I2C reads.
    bool bumper = digitalRead(PIN_BUMPER) == LOW;
    if (bumper && motionActive()) motionStop();

    EdgeReading er;
    sensorsReadEdges(er);
    bumper = bumper || digitalRead(PIN_BUMPER) == LOW;
    bool fault = pcfFaultActive();

    // Battery sags under motor load, so read it only while stopped.
    if (!motionActive() && now - lastBattery > 1000) {
      lastBattery = now;
      float v;
      batteryValid = sensorsReadBattery(v);
      if (batteryValid) battery = v;
    }

    SafetySnapshot s = {};
    s.battery = battery;
    s.batteryValid = batteryValid;
    s.batteryOk = batteryValid && battery >= BATTERY_LOCK_V;
    s.batteryWarn = batteryValid && battery < BATTERY_WARN_V;
    s.sensorsOk = er.ok;
    for (int i = 0; i < 3; i++) {
      s.table[i] = er.table[i];
      s.edgeV[i] = er.diff[i];
    }
    s.bumper = bumper;
    s.fault = fault;

    // ---- Stop conditions while moving ----
    if (motionActive()) {
      Dir d = motionDir();
      if (bumper) hardStop("bumper", "hit");
      else if (fault) hardStop("fault", "driver fault");
      else if (!er.ok) hardStop("sensor", er.problem);
      else if (speakingFlag) { motionStop(); pushEvent("stopped", "speaking", false); }
      else if (!tableOkFor(d, er.table)) { motionStop(); pushEvent("stopped", "edge", false); }
    } else if (patrolOn) {
      if (bumper) hardStop("bumper", "hit");
      else if (fault) hardStop("fault", "driver fault");
      else if (!er.ok) hardStop("sensor", er.problem);
    }
    if (bumper && !lastBumper && !patrolOn) pushEvent("bumper", "pressed", false);
    lastBumper = bumper;

    // ---- Motion finished (timer, stop, or edge) ----
    bool moving = motionActive();
    if (wasMoving && !moving) {
      lastStepEnd = now;
      cyclesAtStop = snap.cycles;
    }
    if (!moving && pcfIsOn(PCF_DRIVER)) pcfSet(PCF_DRIVER, false);
    wasMoving = moving;

    // ---- Battery ----
    if (s.batteryWarn && !warned) {
      warned = true;
      pushEvent("battery", "low", false);
    }
    if (batteryValid && battery >= BATTERY_WARN_V + 0.05f) warned = false;
    if (!s.batteryOk && patrolOn) {
      patrolOn = false;
      pushEvent("patrol", "battery low", false);
    }
    if (batteryValid && battery < BATTERY_SLEEP_V) {
      if (!lowSince) lowSince = now ? now : 1;
      if (now - lowSince > BATTERY_SLEEP_MS) {
        pushEvent("battery", "empty", false);
        lowSince = now;
      }
    } else {
      lowSince = 0;
    }

    // ---- Requests from the laptop ----
    MoveRequest r;
    if (xQueueReceive(requests, &r, 0) == pdTRUE) {
      if (r.dir == Dir::Stop) {
        motionStop();
        pushEvent("move_result", "stopped", true);
      } else if (patrolOn) {
        pushEvent("move_result", "patrol is running", false);
      } else {
        const char *why = checkStart(s, r.dir, r.duty, r.ms);
        if (!why && !startMove(s, r.dir, r.duty, r.ms)) why = "driver did not wake";
        pushEvent("move_result", why ? why : dirName(r.dir), why == nullptr);
      }
    }

    // ---- Patrol: creep, stop, look again ----
    if (patrolOn && !motionActive() && now - lastStepEnd >= PATROL_PAUSE_MS &&
        snap.cycles - cyclesAtStop >= 2) {
      const bool L = er.table[0], R = er.table[1], C = er.table[2];
      Dir step = Dir::Stop;
      uint32_t ms = PATROL_FORWARD_MS;
      if (L && R && C) step = Dir::Forward;
      else if (!L && C && R) { step = Dir::PivotRight; ms = PATROL_PIVOT_MS; }
      else if (!R && C && L) { step = Dir::PivotLeft; ms = PATROL_PIVOT_MS; }

      if (step != Dir::Stop) {
        const char *why = checkStart(s, step, PATROL_DUTY_PERCENT, ms);
        if (why) {
          patrolOn = false;
          pushEvent("patrol", why, false);
        } else {
          startMove(s, step, PATROL_DUTY_PERCENT, ms);
        }
      }
      // Otherwise stop and wait: Bob stays still until the table is seen again or patrol is turned off.
    }

    s.moving = motionActive();
    s.dir = motionDir();
    s.patrol = patrolOn;
    s.unlocked = unlockedFlag;
    s.speaking = speakingFlag;
    portENTER_CRITICAL(&mux);
    s.cycles = snap.cycles + 1;
    snap = s;
    portEXIT_CRITICAL(&mux);

    vTaskDelay(pdMS_TO_TICKS(5));
  }
}

void safetyBegin() {
  pinMode(PIN_BUMPER, INPUT);  // R14 is the pull-up
  requests = xQueueCreate(2, sizeof(MoveRequest));
  events = xQueueCreate(16, sizeof(SafetyEvent));
  // Core 1 with the Arduino loop; Wi-Fi runs on core 0. Priority above loop().
  xTaskCreatePinnedToCore(safetyTask, "safety", 4096, nullptr, 3, nullptr, 1);
}

void safetySuspend() {
  patrolOn = false;
  suspended = true;
  motionStop();
  vTaskDelay(pdMS_TO_TICKS(120));  // let the task finish its current I2C read
}

SafetySnapshot safetyGet() {
  portENTER_CRITICAL(&mux);
  SafetySnapshot s = snap;
  portEXIT_CRITICAL(&mux);
  return s;
}

bool safetyPopEvent(SafetyEvent &e) { return events && xQueueReceive(events, &e, 0) == pdTRUE; }

bool safetyRequestMove(Dir d, int dutyPercent, uint32_t ms) {
  MoveRequest r = {d, dutyPercent, ms};
  return xQueueSend(requests, &r, 0) == pdTRUE;
}

void safetyStopAll(const char *why) {
  motionStop();
  if (patrolOn) pushEvent("patrol", why, false);
  patrolOn = false;
}

void safetySetPatrol(bool on) {
  if (on && !unlockedFlag) {
    pushEvent("patrol", "locked: hold the touch pad 2 s", false);
    return;
  }
  if (!on) motionStop();
  patrolOn = on;
  pushEvent("patrol", on ? "on" : "off", true);
}

void safetySetUnlocked(bool on) {
  unlockedFlag = on;
  if (!on) safetyStopAll("locked");
}

void safetySetSpeaking(bool on) {
  speakingFlag = on;
  if (on) motionStop();
}
