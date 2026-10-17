#pragma once
#include <cmath>
#include <cstdint>

// Platform-independent safety policy, also compiled by the host tests.
enum class Dir : uint8_t { Stop, Forward, PivotLeft, PivotRight };
namespace control {
inline bool elapsed(uint32_t now, uint32_t since, uint32_t interval) {
  return uint32_t(now - since) >= interval;
}
inline bool tableSafe(const bool table[3]) { return table[0] && table[1] && table[2]; }
inline bool batteryValid(float v) { return std::isfinite(v) && v >= 2.5f && v <= 4.30f; }

struct Inputs {
  bool calibrated = false, unlocked = false, link = false, speaking = false;
  bool batteryValid = false, batteryOk = false, sensorsOk = false;
  bool table[3] = {};
  bool bumper = false, fault = false;
};
inline const char *inhibit(const Inputs &s) {
  if (!s.calibrated) return "calibration required";
  if (!s.link) return "link expired";
  if (!s.unlocked) return "locked: hold touch 2 s";
  if (s.speaking) return "speaking";
  if (!s.batteryValid || !s.batteryOk) return "battery unsafe";
  if (!s.sensorsOk) return "sensor invalid or stale";
  if (s.bumper) return "bumper";
  if (s.fault) return "driver fault";
  if (!tableSafe(s.table)) return "edge";
  return nullptr;
}
inline bool validMove(Dir d, int duty, uint32_t ms, int cap, uint32_t forward, uint32_t pivot) {
  if (d != Dir::Forward && d != Dir::PivotLeft && d != Dir::PivotRight) return false;
  return duty > 0 && duty <= cap && ms > 0 && ms <= (d == Dir::Forward ? forward : pivot);
}

// No extensions while active: queued commands cannot prolong a motor pulse.
struct Lease {
  bool active = false;
  uint32_t started = 0, duration = 0, refreshed = 0;
  bool start(uint32_t now, uint32_t ms) {
    if (active || !ms) return false;
    active = true; started = refreshed = now; duration = ms; return true;
  }
  bool expired(uint32_t now, uint32_t safetyMs) const {
    return active && (elapsed(now, started, duration) || elapsed(now, refreshed, safetyMs));
  }
  void stop() { active = false; }
};

// Immediate loss; three NEW valid measurements are required to reacquire.
struct EdgeFilter {
  uint8_t good = 0;
  bool update(bool valid, uint16_t mm, uint16_t minimum, uint16_t maximum, uint16_t hysteresis) {
    if (!valid || minimum >= maximum || mm < minimum || mm > maximum) { good = 0; return false; }
    if (good < 3) {
      if (mm >= minimum + hysteresis && uint32_t(mm) + hysteresis <= maximum) ++good;
      else good = 0;
    }
    return good >= 3;
  }
};
}  // namespace control
