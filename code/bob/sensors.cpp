// Connections: ADS1115 at 0x48 on D4 / D5. A0 left, A1 right, A2 center GP2S700HCP emitters
// (R10-R12 10k and C10-C12 100nF to GND). A3 battery midpoint (R1 / R2 100k, C9).
// Sensor LEDs are switched by PCF8574 P0 (cathodes), anodes through R7-R9 470R to 3V3.
#include "sensors.h"
#include <Adafruit_ADS1X15.h>
#include "bus.h"
#include "config.h"
#include "pcf.h"

static Adafruit_ADS1115 ads;
static bool adsOk = false;
constexpr uint32_t LED_SETTLE_MS = 5;  // R10 x C10 = 1 ms

static bool readChannel(uint8_t ch, float &volts) {
  BusLock lock;
  int16_t raw = ads.readADC_SingleEnded(ch);
  volts = ads.computeVolts(raw);
  return true;
}

bool sensorsBegin() {
  BusLock lock;
  adsOk = ads.begin(ADS_ADDR);
  if (adsOk) {
    ads.setGain(GAIN_ONE);  // +/-4.096 V
    ads.setDataRate(RATE_ADS1115_860SPS);
  }
  return adsOk;
}

bool sensorsReadEdges(EdgeReading &out) {
  out.ok = false;
  out.problem = "adc missing";
  for (int i = 0; i < 3; i++) {
    out.diff[i] = 0;
    out.table[i] = false;
  }
  if (!adsOk) return false;

  float off[3], on[3];
  if (!pcfSet(PCF_LEDS, false)) {
    out.problem = "expander";
    return false;
  }
  vTaskDelay(pdMS_TO_TICKS(LED_SETTLE_MS));
  for (int i = 0; i < 3; i++) readChannel(i, off[i]);

  if (!pcfSet(PCF_LEDS, true)) {
    out.problem = "expander";
    return false;
  }
  vTaskDelay(pdMS_TO_TICKS(LED_SETTLE_MS));
  for (int i = 0; i < 3; i++) readChannel(i, on[i]);

  out.ok = true;
  out.problem = "";
  for (int i = 0; i < 3; i++) {
    out.diff[i] = on[i] - off[i];
    out.table[i] = out.diff[i] > EDGE_THRESHOLD_V[i];
    if (on[i] > SENSOR_SATURATED_V) {
      out.ok = false;
      out.problem = "sensor saturated";
    }
    if (off[i] > SENSOR_AMBIENT_MAX_V) {
      out.ok = false;
      out.problem = "room light";
    }
  }
  return out.ok;
}

bool sensorsReadBattery(float &volts) {
  if (!adsOk) return false;
  float sum = 0, v;
  for (int i = 0; i < 4; i++) {
    readChannel(3, v);
    sum += v;
  }
  volts = sum / 4 * 2.0f * BATTERY_CAL;  // R1 = R2, so the cell is twice the midpoint
  return volts > 0.5f;
}
