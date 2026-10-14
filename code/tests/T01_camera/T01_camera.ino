// T01 — Camera
// Reads the camera ID (OV2640 / OV3660), takes test photos, and optionally
// serves the latest photo at http://<bob-ip>/photo.jpg so you can see it.
//
// Board: XIAO_ESP32S3, PSRAM: OPI PSRAM, USB CDC On Boot: Enabled.

#include <WiFi.h>
#include <WebServer.h>
#include "esp_camera.h"
#include "secrets.h"

// XIAO ESP32-S3 Sense camera connector
#define PWDN_GPIO_NUM  -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  10
#define SIOD_GPIO_NUM  40
#define SIOC_GPIO_NUM  39
#define Y9_GPIO_NUM    48
#define Y8_GPIO_NUM    11
#define Y7_GPIO_NUM    12
#define Y6_GPIO_NUM    14
#define Y5_GPIO_NUM    16
#define Y4_GPIO_NUM    18
#define Y3_GPIO_NUM    17
#define Y2_GPIO_NUM    15
#define VSYNC_GPIO_NUM 38
#define HREF_GPIO_NUM  47
#define PCLK_GPIO_NUM  13

WebServer server(80);

bool cameraBegin() {
  camera_config_t c = {};
  c.pin_d0 = Y2_GPIO_NUM;
  c.pin_d1 = Y3_GPIO_NUM;
  c.pin_d2 = Y4_GPIO_NUM;
  c.pin_d3 = Y5_GPIO_NUM;
  c.pin_d4 = Y6_GPIO_NUM;
  c.pin_d5 = Y7_GPIO_NUM;
  c.pin_d6 = Y8_GPIO_NUM;
  c.pin_d7 = Y9_GPIO_NUM;
  c.pin_xclk = XCLK_GPIO_NUM;
  c.pin_pclk = PCLK_GPIO_NUM;
  c.pin_vsync = VSYNC_GPIO_NUM;
  c.pin_href = HREF_GPIO_NUM;
  c.pin_sccb_sda = SIOD_GPIO_NUM;
  c.pin_sccb_scl = SIOC_GPIO_NUM;
  c.pin_pwdn = PWDN_GPIO_NUM;
  c.pin_reset = RESET_GPIO_NUM;
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

  esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK) {
    Serial.printf("FAIL: esp_camera_init error 0x%x\n", err);
    return false;
  }
  return true;
}

const char *sensorName(uint16_t pid) {
  switch (pid) {
    case OV2640_PID: return "OV2640";
    case OV3660_PID: return "OV3660";
    case OV5640_PID: return "OV5640";
    default: return "unknown";
  }
}

void handlePhoto() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "capture failed");
    return;
  }
  server.setContentLength(fb->len);
  server.send(200, "image/jpeg", "");
  server.client().write(fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== T01 camera ===");

  Serial.printf("PSRAM: %s, %u bytes\n", psramFound() ? "found" : "MISSING", ESP.getPsramSize());
  if (!psramFound()) Serial.println("FAIL: set Tools > PSRAM > OPI PSRAM and upload again.");

  if (!cameraBegin()) {
    Serial.println("Check the camera ribbon is fully seated on the Sense board.");
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  Serial.printf("Camera sensor PID 0x%04x = %s\n", s->id.PID, sensorName(s->id.PID));
  Serial.println("Write this camera name in BOB.md (Phase 1).");

  for (int i = 1; i <= 5; i++) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.printf("Photo %d: FAIL\n", i);
      continue;
    }
    Serial.printf("Photo %d: %ux%u, %u bytes JPEG\n", i, fb->width, fb->height, fb->len);
    esp_camera_fb_return(fb);
    delay(300);
  }

  if (strlen(WIFI_SSID) == 0) {
    Serial.println("PASS if five photos printed. (Set WIFI_SSID to view a photo in a browser.)");
    return;
  }

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Wi-Fi");
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) {
    delay(250);
    Serial.print('.');
  }
  Serial.println();
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi did not connect. Check the name, password, and that it is 2.4 GHz.");
    return;
  }
  server.on("/photo.jpg", handlePhoto);
  server.on("/", []() {
    server.send(200, "text/html",
                "<h2>Bob camera test</h2><img src='/photo.jpg' style='max-width:100%'>"
                "<p>Refresh for a new photo.</p>");
  });
  server.begin();
  Serial.printf("Open http://%s/ in a browser on the same network.\n", WiFi.localIP().toString().c_str());
}

void loop() {
  server.handleClient();
  delay(2);
}
