# T13 — Wi-Fi and laptop link

Connects to Wi-Fi, opens the WebSocket to the laptop server, sends a status every 2 seconds, and prints what the laptop sends back.

![XIAO with antenna](00-xiao-pinout.png)

## Before you start

1. Start the laptop server (see [`../../laptop/README.md`](../../laptop/README.md)):
   ```
   python code\laptop\server.py --no-stt
   ```
2. Find the laptop's IP: run `ipconfig` on the laptop, use the **IPv4 Address** of the Wi-Fi adapter.
3. Copy `secrets.example.h` to `secrets.h`, then put your Wi-Fi name, password and the laptop IP in `secrets.h`. That file stays on this computer.

## Libraries

WebSockets (Markus Sattler), ArduinoJson.

## Steps

1. Upload, open Serial Monitor at 115200.
2. On the laptop, the server prints `Bob connected, firmware T13`.
3. In the laptop server window type: `show Hello|from laptop`

## Expected (Bob's Serial Monitor)

```
Wi-Fi OK, Bob's IP 192.168.1.77, signal -58 dBm
WebSocket connected. PASS step 1.
From laptop: {"type":"show","line1":"Hello!","line2":"laptop connected","ms":3000}
From laptop: {"type":"show","line1":"Hello","line2":"from laptop"}
PASS step 2: a laptop message arrived.
```

## Pass

Both PASS lines appear. The signal is better than about −75 dBm where Bob will drive.

## If it fails

| Symptom | Fix |
| --- | --- |
| Wi-Fi does not connect | 2.4 GHz network only; check the password; antenna fitted. |
| Wi-Fi OK, WebSocket never connects | Wrong laptop IP; Windows Firewall: allow Python on **private** networks when asked, or run `netsh advfirewall firewall add rule name="Bob" dir=in action=allow protocol=TCP localport=8765` in an admin terminal. |
| Connects then drops | Laptop on a guest network that isolates devices; use the main network. |
