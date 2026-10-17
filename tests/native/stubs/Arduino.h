#pragma once
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <functional>
#include <vector>
using std::min; using std::max;
constexpr int D0=1,D1=2,D2=3,D3=4,D4=5,D5=6,D6=43,D7=44,D8=7,D9=8,D10=9;
constexpr int LOW=0,HIGH=1,INPUT=0,OUTPUT=1,pdTRUE=1,portMAX_DELAY=0x7fffffff;
using SemaphoreHandle_t = void*;
extern uint32_t fakeNow;
extern int levels[49];
extern uint32_t duty[49];
extern bool pwmAttachOk, pwmWriteOk;
inline uint32_t millis() { return fakeNow; }
inline void vTaskDelay(uint32_t ms) { fakeNow += ms; }
inline uint32_t pdMS_TO_TICKS(uint32_t ms) { return ms; }
inline void pinMode(int,int) {}
inline void digitalWrite(int pin,int value) { levels[pin]=value; }
inline int digitalRead(int pin) { return levels[pin]; }
inline bool ledcAttachChannel(int,uint32_t,uint8_t,int) { return pwmAttachOk; }
inline bool ledcWrite(int pin,uint32_t value) { if(pwmWriteOk) duty[pin]=value; return pwmWriteOk; }
inline bool ledcDetach(int pin) { duty[pin]=0; return true; }
inline SemaphoreHandle_t xSemaphoreCreateMutex() { return reinterpret_cast<void*>(1); }
inline SemaphoreHandle_t xSemaphoreCreateRecursiveMutex() { return reinterpret_cast<void*>(1); }
inline int xSemaphoreTake(SemaphoreHandle_t,int) { return 1; }
inline int xSemaphoreGive(SemaphoreHandle_t) { return 1; }
inline int xSemaphoreTakeRecursive(SemaphoreHandle_t,int) { return 1; }
inline int xSemaphoreGiveRecursive(SemaphoreHandle_t) { return 1; }

constexpr int LEDC_USE_APB_CLK=0;
inline bool ledcSetClockSource(int) { return true; }
#include <memory>
struct FakeQueue { size_t size,cap; std::vector<std::vector<uint8_t>> entries; };
using QueueHandle_t=FakeQueue*;
inline std::vector<std::unique_ptr<FakeQueue>> queues;
constexpr int pdPASS=1;
inline QueueHandle_t xQueueCreate(size_t cap,size_t size) {
  queues.emplace_back(new FakeQueue{size,cap,{}}); return queues.back().get();
}
inline int xQueueSend(QueueHandle_t q,const void* p,int) {
  if(q->entries.size()>=q->cap) return 0;
  auto* data=static_cast<const uint8_t*>(p);q->entries.emplace_back(data,data+q->size);return 1;
}
inline int xQueueReceive(QueueHandle_t q,void* p,int) {
  if(q->entries.empty())return 0;
  memcpy(p,q->entries.front().data(),q->size);q->entries.erase(q->entries.begin());return 1;
}
inline void xQueueReset(QueueHandle_t q) { q->entries.clear(); }
inline SemaphoreHandle_t xSemaphoreCreateBinary() { return reinterpret_cast<void*>(1); }
inline int xTaskCreatePinnedToCore(void(*)(void*),const char*,int,void*,int,void*,int) { return 1; }
inline void vTaskSuspend(void*) {}
