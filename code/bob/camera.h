#pragma once
#include <Arduino.h>
#include "esp_camera.h"

bool cameraBegin();
const char *cameraName();
camera_fb_t *cameraCapture();  // fresh JPEG; give it back with esp_camera_fb_return()
void cameraEnd();              // standby (OV3660) and deinit before deep sleep
