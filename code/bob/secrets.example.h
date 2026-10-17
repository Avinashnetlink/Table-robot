#pragma once

// Copy this file to secrets.h and edit the three lines before uploading.
// secrets.h is listed in .gitignore so the Wi-Fi password is not pushed.
#define WIFI_SSID "your-wifi"
#define WIFI_PASSWORD "your-password"
#define SERVER_HOST "192.168.1.50"  // laptop IP address (ipconfig on the laptop)

// Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
// Set the same value in the laptop BOB_TOKEN environment variable.
#define BOB_TOKEN ""
