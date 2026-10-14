// T13 — Wi-Fi and the laptop link
// Connects to Wi-Fi, opens the WebSocket to the laptop server
// (code/laptop/server.py), sends a status every 2 s, and prints what the laptop
// sends back. On the laptop console type: show Hello|from laptop
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.
// Libraries: WebSockets (Markus Sattler), ArduinoJson.

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

WebSocketsClient ws;
bool connected = false;
uint32_t lastStatus = 0;

void onEvent(WStype_t type, uint8_t *payload, size_t len) {
  switch (type) {
    case WStype_CONNECTED:
      connected = true;
      Serial.println("WebSocket connected. PASS step 1.");
      ws.sendTXT("{\"type\":\"hello\",\"fw\":\"T13\"}");
      break;
    case WStype_DISCONNECTED:
      if (connected) Serial.println("WebSocket disconnected.");
      connected = false;
      break;
    case WStype_TEXT: {
      JsonDocument doc;
      if (deserializeJson(doc, payload, len)) {
        Serial.printf("Bad JSON: %.*s\n", (int)len, (const char *)payload);
        break;
      }
      const char *t = doc["type"] | "";
      Serial.printf("From laptop: %.*s\n", (int)len, (const char *)payload);
      if (!strcmp(t, "ping")) ws.sendTXT("{\"type\":\"pong\"}");
      if (!strcmp(t, "show")) Serial.println("PASS step 2: a laptop message arrived.");
      break;
    }
    default:
      break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T13 Wi-Fi and laptop link ===");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Wi-Fi");
  for (int i = 0; i < 60 && WiFi.status() != WL_CONNECTED; i++) {
    delay(250);
    Serial.print('.');
  }
  Serial.println();
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("FAIL: Wi-Fi did not connect. Check the name and password; the network must be 2.4 GHz.");
    return;
  }
  Serial.printf("Wi-Fi OK, Bob's IP %s, signal %d dBm\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());
  ws.begin(SERVER_HOST, SERVER_PORT, "/bob");
  ws.onEvent(onEvent);
  ws.setReconnectInterval(3000);
  Serial.printf("Connecting to ws://%s:%u/bob ... start the laptop server if it is not running.\n", SERVER_HOST, SERVER_PORT);
}

void loop() {
  ws.loop();
  if (connected && millis() - lastStatus > 2000) {
    lastStatus = millis();
    JsonDocument doc;
    doc["type"] = "status";
    doc["state"] = "test";
    doc["rssi"] = WiFi.RSSI();
    doc["uptime_s"] = millis() / 1000;
    String s;
    serializeJson(doc, s);
    ws.sendTXT(s);
  }
}
