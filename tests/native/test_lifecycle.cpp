#include <cassert>
#include <iostream>
#include <Wire.h>
#include <esp_timer.h>
#include "safety.h"
#include "bus.h"
// Include the real safety implementation so fixture setup can represent a
// previously armed state without adding any calibration bypass to production.
#include "../../code/bob/safety.cpp"
uint32_t fakeNow=0,duty[49]={};
int levels[49]={};
bool pwmAttachOk=true,pwmWriteOk=true,timerOk=true;
void (*timerCallback)(void*)=nullptr;
FakeWire Wire;
int main() {
  levels[D1]=HIGH;
  assert(motionBegin()); assert(busBegin()); assert(pcfBegin());
  assert(safetyBegin(true));
  assert(!CALIBRATION_CONFIRMED);
  safetyHeartbeat(); safetySetUnlocked(true);
  assert(!safetyRequestMove(Dir::Forward,30,100)); // default firmware never arms
  unlocked=true;  // fixture: existing permitted session
  assert(safetyRequestMove(Dir::Forward,30,100));
  assert(!safetyRequestMove(Dir::Forward,30,100)); // queue bounded
  safetyStopAll("test stop");
  MoveRequest request;
  assert(xQueueReceive(requests,&request,0)==0);
  assert(!unlocked && !patrol && !motionActive());
  assert(!safetyRequestMove(Dir::Forward,30,100));
  unlocked=true; assert(safetyRequestMove(Dir::Forward,30,100));
  safetySetSpeaking(true);
  assert(xQueueReceive(requests,&request,0)==0); assert(!motionActive());
  assert(!safetyGet().unlocked);
  safetySetSpeaking(false);
  unlocked=true; assert(safetyRequestMove(Dir::Forward,30,100));
  assert(safetyRequestMove(Dir::Stop,0,0)); // immediate, even though queue full
  assert(xQueueReceive(requests,&request,0)==0); assert(!unlocked);
  unlocked=true; safetySetPatrol(true); safetySetPatrol(false);
  assert(!patrol && !unlocked);
  auto s=safetyGet(); auto g=inputs(s,millis()); assert(g.link);
  fakeNow=LINK_LEASE_MS; assert(!inputs(s,millis()).link);
  pwmWriteOk=false;
  assert(!motionStart(Dir::Forward,30,100,fakeNow));
  assert(!motionActive() && !motionReady());
  for(int p:{D2,D3,D8,D9}) assert(duty[p]==0 && levels[p]==LOW);
  std::cout<<"PASS real safety lifecycle: factory lock, stop purge, immediate stop, speech purge, patrol stop, heartbeat expiry\n";
}
