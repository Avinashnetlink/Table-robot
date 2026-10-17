# T03 — Upstream bus and three mux branches

Keep motor power isolated. Upload T03 and open Serial Monitor at 115200. It scans the 100 kHz upstream bus with mux branches off, then checks 0x29 separately on channels 0/1/2 and deselects all channels.

Expected upstream addresses: OLED 0x3C, ADS1115 0x48, PCF8574 0x20 (or configured 0x38), TCA9548A 0x70. Expected branch device: one ToF sensor at 0x29 on each of channels 0, 1 and 2.

An ACK proves communication, not sensor identity or valid measurements. The full firmware checks identity and T09 validates ranges. Missing devices require checking the [current wiring](../../../docs/HARDWARE.md), supply, pull-ups and address straps. Press Enter to rescan.
