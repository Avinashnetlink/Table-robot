// T08 — DRV8833 and motors, WHEELS IN THE AIR
// Every run is time-limited. The driver is woken (PCF P2) only during a run.
//   f  forward 300 ms           l  pivot left 250 ms     r  pivot right 250 ms
//   a  left motor fwd 1 s       A  left motor back 1 s
//   b  right motor fwd 1 s      B  right motor back 1 s
//   s  stall test left 1 s 100% S  stall test right 1 s 100%   (hold the shaft, read the ammeter)
//   +  duty +5 %                -  duty -5 %                   x  stop now
//
// Board: XIAO_ESP32S3, USB CDC On Boot: Enabled.

#include <Wire.h>

constexpr uint8_t PIN_AIN1 = D2, PIN_AIN2 = D3, PIN_BIN1 = D8, PIN_BIN2 = D9;
constexpr uint8_t PINS[4] = {PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2};
constexpr uint32_t PWM_HZ = 20000;  // above hearing
constexpr uint8_t PWM_BITS = 10;
constexpr uint8_t P_DRIVER = 1 << 2, P_FAULT = 1 << 3;

uint8_t PCF_ADDR = 0x20;
int dutyPercent = 30;

bool pcfWrite(uint8_t v) {
  Wire.beginTransmission(PCF_ADDR);
  Wire.write(v | P_FAULT | 0xF0);
  return Wire.endTransmission() == 0;
}

bool faultActive() {
  if (Wire.requestFrom(PCF_ADDR, (uint8_t)1) != 1) return true;  // unreadable = unsafe
  return !(Wire.read() & P_FAULT);
}

void setPin(uint8_t i, int percent) {
  ledcWrite(PINS[i], (uint32_t)percent * ((1 << PWM_BITS) - 1) / 100);
}

void allLow() {
  for (uint8_t i = 0; i < 4; i++) setPin(i, 0);
}

// left/right: +duty forward, -duty backward, 0 stop (coast)
void run(int left, int right, uint32_t ms, const char *what) {
  Serial.printf("%s: left %d%%, right %d%%, %lu ms ... ", what, left, right, (unsigned long)ms);
  pcfWrite(0xFF & ~P_DRIVER);  // wake the driver
  delay(2);                    // DRV8833 wake-up time is 1 ms
  setPin(0, left > 0 ? left : 0);
  setPin(1, left < 0 ? -left : 0);
  setPin(2, right > 0 ? right : 0);
  setPin(3, right < 0 ? -right : 0);

  uint32_t start = millis();
  bool fault = false, aborted = false;
  while (millis() - start < ms) {
    if (faultActive()) { fault = true; break; }
    if (Serial.available() && Serial.peek() == 'x') { Serial.read(); aborted = true; break; }
    delay(5);
  }
  allLow();
  pcfWrite(0xFF);  // driver asleep
  Serial.println(fault ? "STOPPED: driver FAULT (overcurrent or overheat)" : aborted ? "stopped by x" : "done");
}

void help() {
  Serial.printf("Duty %d%%. Keys: f l r | a A b B | s S | + - | x\n", dutyPercent);
}

void setup() {
  for (uint8_t i = 0; i < 4; i++) {
    pinMode(PINS[i], OUTPUT);
    digitalWrite(PINS[i], LOW);
    // Channels 0-3 use LEDC timers 0 and 1; the camera uses timer 3.
    ledcAttachChannel(PINS[i], PWM_HZ, PWM_BITS, i);
    ledcWrite(PINS[i], 0);
  }
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T08 motors - WHEELS IN THE AIR ===");
  Wire.begin();
  if (!pcfWrite(0xFF)) {
    PCF_ADDR = 0x38;
    if (!pcfWrite(0xFF)) {
      Serial.println("FAIL: no PCF8574. The driver cannot be woken. Run T07 first.");
      while (true) delay(1000);
    }
  }
  Serial.printf("Driver fault line: %s\n", faultActive() ? "FAULT - check R21 and FLT wire" : "OK");
  Serial.println("Reset test: press the XIAO reset button during a run - the wheels must stop at once.");
  help();
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  int d = dutyPercent;
  switch (c) {
    case 'f': run(d, d, 300, "Forward"); break;
    case 'l': run(0, d, 250, "Pivot left"); break;
    case 'r': run(d, 0, 250, "Pivot right"); break;
    case 'a': run(d, 0, 1000, "Left motor forward"); break;
    case 'A': run(-d, 0, 1000, "Left motor backward"); break;
    case 'b': run(0, d, 1000, "Right motor forward"); break;
    case 'B': run(0, -d, 1000, "Right motor backward"); break;
    case 's': run(100, 0, 1000, "STALL left (hold the shaft)"); break;
    case 'S': run(0, 100, 1000, "STALL right (hold the shaft)"); break;
    case '+': dutyPercent = min(100, dutyPercent + 5); help(); break;
    case '-': dutyPercent = max(0, dutyPercent - 5); help(); break;
    case 'x': allLow(); pcfWrite(0xFF); Serial.println("Stopped."); break;
    default: break;
  }
}
