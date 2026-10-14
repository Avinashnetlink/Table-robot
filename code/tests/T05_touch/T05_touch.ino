// T05 — Copper touch pad on D0 (through R13 470 ohm)
// Measures the pad untouched and touched, then prints the numbers to copy
// into code/bob/config.h: TOUCH_IDLE, TOUCH_PRESS_DELTA, TOUCH_WAKE_DELTA.
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.

constexpr uint8_t PIN_TOUCH = D0;  // GPIO1, touch channel 1

uint32_t average(uint32_t ms) {
  uint64_t sum = 0;
  uint32_t n = 0, end = millis() + ms;
  while (millis() < end) {
    sum += touchRead(PIN_TOUCH);
    n++;
    delay(10);
  }
  return n ? sum / n : 0;
}

uint32_t idle = 0, pressed = 0, pressDelta = 0;

void calibrate() {
  Serial.println("\nDo NOT touch the pad. Measuring for 3 s...");
  delay(500);
  idle = average(3000);
  Serial.printf("Untouched: %lu\n", (unsigned long)idle);

  Serial.println("Now TOUCH and HOLD the pad with one finger. Starting in 2 s...");
  delay(2000);
  pressed = average(3000);
  Serial.printf("Touched:   %lu\n", (unsigned long)pressed);

  if (pressed <= idle) {
    Serial.println("FAIL: touching did not raise the reading. Check the D0 wire, R13, and that the pad is not grounded.");
    return;
  }
  uint32_t delta = pressed - idle;
  float ratio = (float)pressed / idle;
  pressDelta = delta / 2;
  Serial.printf("Change: +%lu (x%.2f). %s\n", (unsigned long)delta, ratio,
                ratio > 1.2f ? "PASS - clear change" : "WEAK - shorten the wire or enlarge the pad");

  Serial.println("\nCopy into code/bob/config.h:");
  Serial.printf("  constexpr uint32_t TOUCH_IDLE        = %lu;\n", (unsigned long)idle);
  Serial.printf("  constexpr uint32_t TOUCH_PRESS_DELTA = %lu;\n", (unsigned long)pressDelta);
  Serial.printf("  constexpr uint32_t TOUCH_WAKE_DELTA  = %lu;\n", (unsigned long)(delta * 4 / 10));
  Serial.println("\nLive readings follow. Press Enter to calibrate again.");
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T05 touch pad ===");
  calibrate();
}

void loop() {
  if (Serial.available()) {
    while (Serial.available()) Serial.read();
    calibrate();
  }
  uint32_t v = touchRead(PIN_TOUCH);
  bool on = pressDelta && v > idle + pressDelta;
  Serial.printf("touch:%lu %s\n", (unsigned long)v, on ? "TOUCHED" : "");
  delay(100);
}
