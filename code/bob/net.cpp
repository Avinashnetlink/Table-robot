#include "net.h"
#include <WiFi.h>
#include <WebSocketsClient.h>
#include "config.h"
#include "secrets.h"
#include "safety.h"
#include "audio.h"
#ifndef BOB_TOKEN
#define BOB_TOKEN ""
#endif
static WebSocketsClient ws;
static TextHandler textHandler = nullptr;
static BinaryHandler binaryHandler = nullptr;
static bool wsOpen = false, authenticated = false, wsStarted = false;
static uint32_t lastSequence = 0, lastWifiAttempt = 0;
static uint8_t *txBuf = nullptr;
static size_t txCap = 0;
static String headers;
static void disconnected() {
  if (wsOpen || authenticated) { safetyStopAll("link lost"); speakerEnd(); }
  wsOpen = authenticated = false;
}
static void onEvent(WStype_t type, uint8_t *payload, size_t len) {
  switch (type) {
    case WStype_CONNECTED: {
      wsOpen = true; authenticated = false; lastSequence = 0;
      safetyStopAll("new session");
      JsonDocument hello;
      hello["type"] = "hello"; hello["fw"] = FIRMWARE;
      String s; serializeJson(hello, s); ws.sendTXT(s);
      break;
    }
    case WStype_DISCONNECTED: disconnected(); break;
    case WStype_TEXT: {
      if (len > MAX_TEXT_BYTES) { ws.disconnect(); break; }
      JsonDocument doc;
      if (deserializeJson(doc, payload, len, DeserializationOption::NestingLimit(4)) || !doc.is<JsonObject>()) break;
      if (!doc["token"].is<const char *>() || strcmp(doc["token"], BOB_TOKEN) ||
          !doc["seq"].is<uint32_t>() || !doc["type"].is<const char *>()) break;
      uint32_t seq = doc["seq"];
      if (!seq || seq <= lastSequence) break;
      lastSequence = seq;
      const char *t = doc["type"];
      if (!strcmp(t, "ping")) { authenticated = true; safetyHeartbeat(); }
      if (authenticated && textHandler) textHandler(doc);
      break;
    }
    case WStype_BIN:
      if (authenticated && len > 1 && len <= MAX_PLAY_BYTES + 1 && payload[0] == TAG_PLAY &&
          ((len - 1) % 2 == 0) && binaryHandler) binaryHandler(payload[0], payload + 1, len - 1);
      break;
    case WStype_FRAGMENT_TEXT_START:
    case WStype_FRAGMENT_BIN_START:
      ws.disconnect(); break;  // protocol uses complete frames, never unbounded reassembly
    default: break;
  }
}
void netBegin(TextHandler onText, BinaryHandler onBinary) {
  textHandler = onText; binaryHandler = onBinary;
  if (strlen(BOB_TOKEN) < 32) { Serial.println("Network disabled: set BOB_TOKEN (32+ characters) in secrets.h"); return; }
  WiFi.mode(WIFI_STA); WiFi.setAutoReconnect(true); WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD); lastWifiAttempt = millis();
}
void netLoop() {
  if (strlen(BOB_TOKEN) < 32) return;
  if (WiFi.status() != WL_CONNECTED) {
    if (wsOpen) ws.disconnect();
    disconnected();
    if (millis() - lastWifiAttempt > 10000) { lastWifiAttempt = millis(); WiFi.reconnect(); }
    return;
  }
  if (!wsStarted) {
    headers = String("Authorization: Bearer ") + BOB_TOKEN + "\r\n";
    ws.begin(SERVER_HOST, SERVER_PORT, SERVER_PATH);
    ws.setExtraHeaders(headers.c_str());
    ws.onEvent(onEvent); ws.setReconnectInterval(3000); ws.enableHeartbeat(2000, 1000, 2);
    wsStarted = true;
  }
  ws.loop();
}
bool netWifiUp() { return WiFi.status() == WL_CONNECTED; }
bool netConnected() { return wsOpen && authenticated; }
void netSend(JsonDocument &doc) {
  if (!netConnected()) return;
  String s; serializeJson(doc, s); ws.sendTXT(s);
}
bool netSendBinary(uint8_t tag, const uint8_t *data, size_t len) {
  if (!netConnected() || !data || !len || len > MAX_IMAGE_BYTES) return false;
  if (txCap < len + 1) {
    auto *next = static_cast<uint8_t *>(psramFound() ? ps_malloc(len + 1) : malloc(len + 1));
    if (!next) return false;
    free(txBuf); txBuf = next; txCap = len + 1;
  }
  txBuf[0] = tag; memcpy(txBuf + 1, data, len);
  return ws.sendBIN(txBuf, len + 1);
}
void netEnd() {
  if (wsStarted) ws.disconnect();
  disconnected(); wsStarted = false;
  free(txBuf); txBuf = nullptr; txCap = 0;
  WiFi.disconnect(true); WiFi.mode(WIFI_OFF);
}
