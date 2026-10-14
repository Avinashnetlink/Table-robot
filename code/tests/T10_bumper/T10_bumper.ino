// T10 — Bumper microswitches on D1 (R14 10k pull-up, C14 100 nF)
// Prints every press and release. Press each switch on its own.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.

constexpr uint8_t PIN_BUMPER = D1;
constexpr uint32_t DEBOUNCE_MS = 15;

bool lastPressed = false;
uint32_t changedAt = 0, presses = 0;

void setup() {
  pinMode(PIN_BUMPER, INPUT);  // R14 is the pull-up; no internal pull needed
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T10 bumper ===");
  lastPressed = digitalRead(PIN_BUMPER) == LOW;
  if (lastPressed) {
    Serial.println("FAIL: D1 is low with nothing pressed. Check R14 to 3V3, or a switch wired to NC instead of NO.");
  } else {
    Serial.println("Idle = high, OK. Press the left switch, then the right switch.");
  }
}

void loop() {
  bool pressed = digitalRead(PIN_BUMPER) == LOW;
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
