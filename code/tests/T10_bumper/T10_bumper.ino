#include <Wire.h>
// T10 — Bumper microswitches on D1 (R14 10k pull-up, C14 100 nF)
// Prints every press and release. Press each switch on its own.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.

constexpr uint8_t PIN_BUMPER = D1;
constexpr bool BUMPER_NC_SERIES = false;  // set true for optional series-NC wiring
constexpr uint32_t DEBOUNCE_MS = 15;

bool lastPressed = false;
uint32_t changedAt = 0, presses = 0;


// Reset the retained expander latch BEFORE any startup delay.
static void benchSafeBoot() {
  for (int p : {D2, D3, D8, D9}) { digitalWrite(p, LOW); pinMode(p, OUTPUT); }
  Wire.begin(D4, D5, 100000); Wire.setTimeOut(10);
  for (uint8_t a : {0x20, 0x38}) {
    Wire.beginTransmission(a); Wire.write(0xFF); Wire.endTransmission();
  }
}

void setup() {
  benchSafeBoot();
  pinMode(PIN_BUMPER, INPUT);  // R14 is the pull-up; no internal pull needed
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T10 bumper ===");
  lastPressed = digitalRead(PIN_BUMPER) == (BUMPER_NC_SERIES ? HIGH : LOW);
  if (lastPressed) {
    Serial.println("FAIL: bumper reports pressed/open. Check contacts and selected NO/NC mode.");
  } else {
    Serial.println("Idle level matches selected contact mode, OK. Press the left switch, then the right switch.");
  }
}

void loop() {
  bool pressed = digitalRead(PIN_BUMPER) == (BUMPER_NC_SERIES ? HIGH : LOW);
  if (pressed != lastPressed && millis() - changedAt > DEBOUNCE_MS) {
    changedAt = millis();
    lastPressed = pressed;
    if (pressed) {
      presses++;
      Serial.printf("PRESSED  (#%lu) -> Bob would stop\n", (unsigned long)presses);
    } else {
      Serial.println("released");
    }
    if (presses >= 2 && !pressed) Serial.println("PASS if both switches each printed one press.");
  }
  delay(1);
}
