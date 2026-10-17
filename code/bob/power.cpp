// Connections: copper pad on D0 (GPIO1, touch 1) through R13 470R. It is the only wake source.
#include "power.h"
#include "esp_sleep.h"
#include "audio.h"
#include "camera.h"
#include "config.h"
#include "display.h"
#include "net.h"
#include "pcf.h"
#include "safety.h"
#include "sensors.h"

static float baseline = TOUCH_IDLE;
static bool down = false, holdFired = false;
static uint32_t downAt = 0, lastRead = 0;

void touchBegin() {
  // If Bob was woken by a touch the finger may still be on the pad,
  // so start from the calibrated idle value and adapt slowly.
  baseline = TOUCH_IDLE;
}

TouchEvent touchService() {
  uint32_t now = millis();
  if (now - lastRead < 40) return TouchEvent::None;
  lastRead = now;

  uint32_t v = touchRead(PIN_TOUCH);
  if (v == 0) return TouchEvent::None;
  bool pressed = v > baseline + TOUCH_PRESS_DELTA;
  if (!pressed) baseline += (v - baseline) * 0.01f;  // follow slow drift (humidity, temperature)

  TouchEvent ev = TouchEvent::None;
  if (pressed && !down) {
    down = true;
    holdFired = false;
    downAt = now;
    ev = TouchEvent::Press;
  } else if (pressed && down && !holdFired && now - downAt >= UNLOCK_HOLD_MS) {
    holdFired = true;
    ev = TouchEvent::Hold;
  } else if (!pressed && down) {
    down = false;
    if (!holdFired && now - downAt >= 60) ev = TouchEvent::Tap;
  }
  return ev;
}

bool touchDown() { return down; }

const char *wakeReason() {
  switch (esp_sleep_get_wakeup_cause()) {
    case ESP_SLEEP_WAKEUP_TOUCHPAD: return "touch";
    case ESP_SLEEP_WAKEUP_UNDEFINED: return "power on";
    default: return "other";
  }
}

void powerSleepNow() {
  if (!safetySuspend()) {
    Serial.println("Safety task did not acknowledge sleep; restarting with motors off");
    ESP.restart();
    while (true) delay(1);
  }
  edgesEnd();
  audioEnd();        // amp off
  pcfReleaseAll();   // amp and driver off; the PCF8574 keeps this through sleep
  displayOff();
  cameraEnd();
  netEnd();
  Serial.println("Sleeping. Touch the pad to wake.");
  Serial.flush();
  touchSleepWakeUpEnable(PIN_TOUCH, TOUCH_WAKE_DELTA);
  esp_deep_sleep_start();
}
