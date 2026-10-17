#pragma once

// Copy this file to secrets.h and edit the three lines before uploading.
// secrets.h is listed in .gitignore so the Wi-Fi password is not pushed.
const char *WIFI_SSID = "your-wifi";
const char *WIFI_PASSWORD = "your-password";
const char *SERVER_HOST = "192.168.1.50";  // laptop IP address (ipconfig on the laptop)
constexpr uint16_t SERVER_PORT = 8765;

#define BOB_TOKEN ""  // same token as the laptop, 32+ characters
