// Connections: Wi-Fi through the antenna on the XIAO (2.4 GHz). WebSocket to ws://SERVER_HOST:8765/bob.
#include "net.h"
#include <WiFi.h>
#include <WebSocketsClient.h>
#include "config.h"
#include "secrets.h"

static WebSocketsClient ws;
static TextHandler textHandler = nullptr;
static BinaryHandler binaryHandler = nullptr;
static bool wsOpen = false, wsStarted = false;
static uint8_t *txBuf = nullptr;
static size_t txCap = 0;

static void onEvent(WStype_t type, uint8_t *payload, size_t len) {
  switch (type) {
    case WStype_CONNECTED: {
      wsOpen = true;
      JsonDocument hello;
      hello["type"] = "hello";
      hello["fw"] = FIRMWARE;
      netSend(hello);
      break;
    }
    case WStype_DISCONNECTED:
      wsOpen = false;
      break;
    case WStype_TEXT: {
      JsonDocument doc;
      if (!deserializeJson(doc, payload, len) && textHandler) textHandler(doc);
      break;
    }
    case WStype_BIN:
      if (len > 0 && binaryHandler) binaryHandler(payload[0], payload + 1, len - 1);
      break;
    default:
      break;
  }
}

void netBegin(TextHandler onText, BinaryHandler onBinary) {
  textHandler = onText;
  binaryHandler = onBinary;
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

void netLoop() {
  if (WiFi.status() != WL_CONNECTED) {
    wsOpen = false;
    return;
  }
  if (!wsStarted) {
    ws.begin(SERVER_HOST, SERVER_PORT, SERVER_PATH);
    ws.onEvent(onEvent);
    ws.setReconnectInterval(5000);
    ws.enableHeartbeat(15000, 3000, 2);
    wsStarted = true;
  }
  ws.loop();
}

bool netWifiUp() { return WiFi.status() == WL_CONNECTED; }
bool netConnected() { return wsOpen; }

void netSend(JsonDocument &doc) {
  if (!wsOpen) return;
  String s;
  serializeJson(doc, s);
  ws.sendTXT(s);
}

bool netSendBinary(uint8_t tag, const uint8_t *data, size_t len) {
  if (!wsOpen) return false;
  if (txCap < len + 1) {
    free(txBuf);
    txCap = len + 1;
    txBuf = (uint8_t *)(psramFound() ? ps_malloc(txCap) : malloc(txCap));
    if (!txBuf) {
      txCap = 0;
      return false;
    }
  }
  txBuf[0] = tag;
  memcpy(txBuf + 1, data, len);
  return ws.sendBIN(txBuf, len + 1);
}

void netEnd() {
  if (wsStarted) ws.disconnect();
  wsOpen = false;
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
}
