#include <ArduinoJson.h>
#include <WiFi.h>
#include "diagnostics.h"
#include "audio.h"
#include "config.h"
#include "net.h"
#include "safety.h"
#include "sensors.h"
#include "wiring.h"
void diagnosticsStatus() {
  SafetySnapshot s = safetyGet();
  JsonDocument doc;
  doc["type"] = "status";
  doc["state"] = speaking() ? "speaking" : s.moving ? "moving" : "awake";
  doc["battery_v"] = serialized(String(s.battery, 2));
  doc["battery_valid"] = s.batteryValid;
  doc["calibrated"] = s.calibrated;
  doc["link_ok"] = s.linkOk;
  doc["cycle_ms"] = s.cycleMs;
  doc["max_cycle_ms"] = s.maxCycleMs;
  doc["stop_reason"] = s.stopReason ? s.stopReason : "boot";
  doc["edge_sensor"] = edgeSensorName();
  doc["heap_free"] = ESP.getFreeHeap();
  doc["uptime_ms"] = millis();
  doc["battery_low"] = s.batteryWarn;
  doc["sensors_ok"] = s.sensorsOk;
  JsonArray table = doc["table"].to<JsonArray>();
  JsonArray edge = doc["edge_mm"].to<JsonArray>();
  JsonArray valid = doc["edge_valid"].to<JsonArray>();
  JsonArray status = doc["edge_status"].to<JsonArray>();
  for (int i = 0; i < 3; i++) {
    table.add(s.table[i]);
    edge.add(s.edgeMm[i]); valid.add(s.edgeValid[i]); status.add(s.edgeStatus[i]);
  }
  doc["bumper"] = s.bumper;
  doc["fault"] = s.fault;
  doc["unlocked"] = s.unlocked;
  doc["patrol"] = s.patrol;
  doc["moving"] = s.moving;
  doc["rssi"] = WiFi.RSSI();
  if (Serial) { serializeJson(doc, Serial); Serial.println(); }
  netSend(doc);
}


void diagnosticsService() {
  static char line[32];
  static size_t used = 0;
  static bool overflow = false;
  for (int count = 0; count < 32 && Serial.available(); ++count) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      line[used] = 0;
      if (!overflow && !strcmp(line, "status")) diagnosticsStatus();
      else if (!overflow && !strcmp(line, "stop")) { safetyStopAll("serial stop"); diagnosticsStatus(); }
      else if (!overflow && !strcmp(line, "wiring")) wiringPrint();
      else Serial.println("Commands: status, stop, wiring. Unlock only by physical touch.");
      used = 0; overflow = false;
    } else if (used < sizeof(line)-1) line[used++] = c;
    else overflow = true;
  }
}
