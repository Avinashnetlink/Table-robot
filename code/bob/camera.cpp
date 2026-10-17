// Connections: the Sense board camera ribbon only. No header pins are used.
#include "camera.h"

static bool ok = false;

bool cameraBegin() {
  if (!psramFound()) return false;
  camera_config_t c = {};
  // XIAO ESP32-S3 Sense camera connector
  c.pin_d0 = 15;
  c.pin_d1 = 17;
  c.pin_d2 = 18;
  c.pin_d3 = 16;
  c.pin_d4 = 14;
  c.pin_d5 = 12;
  c.pin_d6 = 11;
  c.pin_d7 = 48;
  c.pin_xclk = 10;
  c.pin_pclk = 13;
  c.pin_vsync = 38;
  c.pin_href = 47;
  c.pin_sccb_sda = 40;
  c.pin_sccb_scl = 39;
  c.pin_pwdn = -1;
  c.pin_reset = -1;
  c.xclk_freq_hz = 20000000;
  // Timer 3 / channel 7 keeps the camera clock away from the motor PWM channels 0-3.
  c.ledc_timer = LEDC_TIMER_3;
  c.ledc_channel = LEDC_CHANNEL_7;
  c.pixel_format = PIXFORMAT_JPEG;
  c.frame_size = FRAMESIZE_VGA;
  c.jpeg_quality = 12;
  c.fb_count = 1;
  c.fb_location = CAMERA_FB_IN_PSRAM;
  c.grab_mode = CAMERA_GRAB_LATEST;
  ok = esp_camera_init(&c) == ESP_OK;
  return ok;
}

const char *cameraName() {
  if (!ok) return "none";
  sensor_t *s = esp_camera_sensor_get();
  if (!s) return "none";
  switch (s->id.PID) {
    case OV2640_PID: return "OV2640";
    case OV3660_PID: return "OV3660";
    case OV5640_PID: return "OV5640";
    default: return "unknown";
  }
}

camera_fb_t *cameraCapture() {
  if (!ok) return nullptr;
  camera_fb_t *old = esp_camera_fb_get();  // may be stale; take a fresh one
  if (!old) return nullptr;
  esp_camera_fb_return(old);
  camera_fb_t *fb = esp_camera_fb_get();
  if (fb && (fb->format != PIXFORMAT_JPEG || !fb->buf || fb->len < 4 || fb->len > 512 * 1024)) {
    esp_camera_fb_return(fb); return nullptr;
  }
  return fb;
}

void cameraEnd() {
  if (!ok) return;
  sensor_t *s = esp_camera_sensor_get();
  // OV3660 system control 0x3008 bit 6 = software power down.
  if (s && s->id.PID == OV3660_PID) s->set_reg(s, 0x3008, 0x40, 0x40);
  esp_camera_deinit();
  ok = false;
}
