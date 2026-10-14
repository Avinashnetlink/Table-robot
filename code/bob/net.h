#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

using TextHandler = void (*)(JsonDocument &msg);
using BinaryHandler = void (*)(uint8_t tag, const uint8_t *data, size_t len);

void netBegin(TextHandler onText, BinaryHandler onBinary);
void netLoop();
bool netWifiUp();
bool netConnected();  // WebSocket to the laptop is open
void netSend(JsonDocument &doc);
bool netSendBinary(uint8_t tag, const uint8_t *data, size_t len);
void netEnd();
