// Bob — complete firmware for the XIAO ESP32-S3 Sense table robot.
// See README.md in this folder for setup, libraries and the laptop protocol.
//
// Board: XIAO_ESP32S3, PSRAM: OPI PSRAM, USB CDC On Boot: Enabled,
//        Partition scheme: default 8 MB (3 MB application).

#include <WiFi.h>
#include <Wire.h>
#include "esp_task_wdt.h"
#include "audio.h"
#include "bus.h"
#include "camera.h"
#include "config.h"
#include "display.h"
#include "motion.h"
#include "net.h"
#include "pcf.h"
#include "power.h"
#include "safety.h"
#include "sensors.h"
#include "wiring.h"
#include "diagnostics.h"

static uint32_t lastActivity = 0, lastStatus = 0;
static bool wasConnected = false;
static int16_t micBuf[MIC_CHUNK_SAMPLES];

static void activity() { lastActivity = millis(); }

static void sendEvent(const char *what, const char *detail, bool ok) {
  JsonDocument doc;
  doc["type"] = "event";
  doc["what"] = what;
  doc["detail"] = detail;
  doc["ok"] = ok;
  netSend(doc);
}

static void sendPhoto() {
  safetyStopAll("photo");
  camera_fb_t *fb = cameraCapture();
  if (!fb) {
    sendEvent("photo", "camera failed", false);
    return;
  }
  bool sent = netSendBinary(TAG_IMAGE, fb->buf, fb->len);
  esp_camera_fb_return(fb);
  if (!sent) sendEvent("photo", "send failed", false);
}

// ---------- Messages from the laptop ----------
static void onText(JsonDocument &msg) {
  const char *type = msg["type"] | "";

  if (!strcmp(type, "ping")) {
    JsonDocument r;
    r["type"] = "pong";
    netSend(r);
    return;  // a ping is not activity
  }
  activity();

  if (!strcmp(type, "show")) {
    displaySetText(msg["line1"] | "", msg["line2"] | "", msg["ms"] | 8000);
  } else if (!strcmp(type, "state")) {
    displaySetMood(msg["state"] | "awake");
  } else if (!strcmp(type, "listen")) {
    displaySetMood(msg["active"] | false ? "listening" : "awake");
  } else if (!strcmp(type, "say_start")) {
    safetyStopAll("speech");
  } else if (!strcmp(type, "say_end")) {
    speakerEnd();
    safetySetSpeaking(false);
  } else if (!strcmp(type, "move")) {
    Dir d;
    if (!parseDir(msg["dir"] | "", d)) {
      sendEvent("move_result", "unknown direction (reverse is disabled)", false);
    } else if (d != Dir::Stop && (!msg["duty"].is<int>() || !msg["ms"].is<uint32_t>())) {
      sendEvent("move_result", "invalid numeric fields", false);
    } else if (!safetyRequestMove(d, msg["duty"] | 0, msg["ms"] | 0)) {
      sendEvent("move_result", "busy", false);
    }
  } else if (!strcmp(type, "patrol")) {
    if (msg["on"].is<bool>()) safetySetPatrol(msg["on"].as<bool>());
  } else if (!strcmp(type, "stop")) {
    safetyStopAll("laptop stop");
  } else if (!strcmp(type, "photo")) {
    sendPhoto();
  } else if (!strcmp(type, "status")) {
    diagnosticsStatus();
  } else if (!strcmp(type, "sleep")) {
    powerSleepNow();
  }
  // "keep_awake" and anything unknown only count as activity.
}

static void onBinary(uint8_t tag, const uint8_t *data, size_t len) {
  if (tag == TAG_PLAY) {
    activity();
    speakerPlay(data, len);
  }
}

// ---------- Setup ----------
static bool startWatchdog() {
  esp_task_wdt_config_t cfg = {};
  cfg.timeout_ms = WDT_TIMEOUT_MS;
  cfg.idle_core_mask = 0;
  cfg.trigger_panic = true;  // a hung task resets the board; the 100k pulldowns then stop the wheels
  if (esp_task_wdt_reconfigure(&cfg) != ESP_OK && esp_task_wdt_init(&cfg) != ESP_OK) return false;
  return esp_task_wdt_add(nullptr) == ESP_OK;
}

void setup() {
  bool motorOk = motionBegin();  // motor inputs low before anything else
  Serial.begin(115200);
  bool busOk = busBegin();
  bool pcfOk = pcfBegin();  // the PCF8574 kept its old outputs through the reset
  delay(300);
  Serial.printf("\nBob %s, woke by %s\n", FIRMWARE, wakeReason());

  bool oledOk = displayBegin();
  displaySetText("Hello!", wakeReason(), 3000);
  displaySetMood("offline");
  bool adsOk = sensorsBegin();
  bool edgeOk = edgesBegin();
  touchBegin();
  bool audioOk = audioBegin();
  bool camOk = cameraBegin();
  Serial.printf("PCF8574 %s, OLED %s, ADS1115 %s, audio %s, camera %s\n", pcfOk ? "ok" : "MISSING",
                oledOk ? "ok" : "MISSING", adsOk ? "ok" : "MISSING", audioOk ? "ok" : "FAIL", cameraName());
  if (!pcfOk || !adsOk) Serial.println("Motion stays disabled: the expander or ADC is missing.");

  wiringCheck(pcfOk, oledOk, adsOk, edgeOk, audioOk, camOk);
  wiringPrint();
  if (wiringProblems()) displaySetText("Wiring!", wiringFirstProblem(), 6000);
  else displaySetText("Hello!", "bench checks due", 3000);

  bool watchdogOk = startWatchdog();  // before the safety task starts, so it can subscribe
  if (!safetyBegin(watchdogOk && busOk && motorOk && pcfOk && adsOk && edgeOk)) {
    motionStop(); pcfReleaseAll();
    Serial.println("FATAL: safety task allocation failed");
    while (true) { esp_task_wdt_reset(); delay(100); }
  }
  netBegin(onText, onBinary);
  activity();
}

// ---------- Loop ----------
void loop() {
  esp_task_wdt_reset();
  uint32_t now = millis();

  diagnosticsService();
  netLoop();
  bool connected = netConnected();
  if (connected != wasConnected) {
    wasConnected = connected;
    displaySetMood(connected ? "awake" : "offline");
    if (connected) {
      JsonDocument report;
      wiringToJson(report);
      netSend(report);
    } else {
      safetyStopAll("laptop link lost");
    }
  }

  switch (touchService()) {
    case TouchEvent::Press:
      safetyStopAll("touch press");
      activity();
      break;
    case TouchEvent::Hold:
      safetySetUnlocked(true);
      displaySetText("Drive", safetyGet().unlocked ? "unlocked" : "locked - see log", 2000);
      sendEvent("touch", "hold", true);
      activity();
      break;
    case TouchEvent::Tap: {
      SafetySnapshot s = safetyGet();
      if (s.patrol || s.moving || s.unlocked) {
        safetyStopAll("touch");
        displaySetText("Stopped", "by touch", 2000);
      }
      sendEvent("touch", "tap", true);
      activity();
      break;
    }
    default:
      break;
  }

  SafetyEvent e;
  while (safetyPopEvent(e)) {
    sendEvent(e.what, e.detail, e.ok);
    Serial.printf("[%s] %s\n", e.what, e.detail);
    if (!strcmp(e.what, "bumper") || !strcmp(e.what, "fault") || !strcmp(e.what, "sensor") || !strcmp(e.what, "stopped")) {
      displaySetText("Stop!", e.detail, 3000);
    } else if (!strcmp(e.what, "battery")) {
      if (!strcmp(e.detail, "empty")) powerSleepNow();
      displaySetText("Battery", "low - charge me", 5000);
    }
  }

  audioService();
  if (connected && micAllowed()) {
    size_t n = micRead(micBuf, MIC_CHUNK_SAMPLES);
    if (n) netSendBinary(TAG_MIC, (const uint8_t *)micBuf, n * sizeof(int16_t));
  } else {
    delay(5);
  }

  SafetySnapshot s = safetyGet();
  if (now - lastStatus > STATUS_EVERY_MS) {
    lastStatus = now;
    diagnosticsStatus();
  }
  if (s.sleepRequested) powerSleepNow();
  displayUpdate(s.battery, s.batteryWarn, netWifiUp(), s.unlocked, s.patrol);

  bool busy = s.patrol || s.moving || speaking() || touchDown();
  if (busy) activity();
  if (millis() - lastActivity > SLEEP_AFTER_MS) powerSleepNow();
}
