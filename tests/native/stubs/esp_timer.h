#pragma once
#include <cstdint>
constexpr int ESP_OK=0;
using esp_timer_handle_t=void*;
struct esp_timer_create_args_t { void (*callback)(void*)=nullptr; const char* name=nullptr; };
extern void (*timerCallback)(void*);
extern bool timerOk;
inline int esp_timer_create(const esp_timer_create_args_t* args,esp_timer_handle_t* h) {
  timerCallback=args->callback;*h=reinterpret_cast<void*>(1);return timerOk?0:1;
}
inline int esp_timer_start_periodic(esp_timer_handle_t,uint64_t) { return timerOk?0:1; }
