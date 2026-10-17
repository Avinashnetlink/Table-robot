#include <cassert>
#include <iostream>
#include <limits>
#include <Wire.h>
#include "control.h"
#include "config.h"
#include "motion.h"
#include "bus.h"
#include "pcf.h"
#include "sensors.h"
uint32_t fakeNow=0, duty[49]={};
int levels[49]={};
bool pwmAttachOk=true,pwmWriteOk=true,timerOk=true;
void (*timerCallback)(void*)=nullptr;
FakeWire Wire;
static void stopped() { for(int p:{D2,D3,D8,D9}) assert(duty[p]==0); assert(!motionActive()); }
int main() {
  control::Inputs s;
  s.calibrated=s.unlocked=s.link=s.batteryValid=s.batteryOk=s.sensorsOk=true;
  s.table[0]=s.table[1]=s.table[2]=true;
  assert(!control::inhibit(s));
  for (int mask=0;mask<8;++mask) {
    for(int i=0;i<3;++i) s.table[i]=mask&(1<<i);
    assert((control::inhibit(s)==nullptr)==(mask==7));
  }
  s.table[0]=s.table[1]=s.table[2]=true;
  for(bool* flag:{&s.calibrated,&s.unlocked,&s.link,&s.batteryValid,&s.batteryOk,&s.sensorsOk}) {
    *flag=false; assert(control::inhibit(s)); *flag=true;
  }
  for(bool* flag:{&s.speaking,&s.bumper,&s.fault}) {
    *flag=true; assert(control::inhibit(s)); *flag=false;
  }
  assert(!control::batteryValid(std::numeric_limits<float>::quiet_NaN()));
  assert(!control::batteryValid(4.31f)); assert(!control::batteryValid(0));
  assert(control::validMove(Dir::Forward,40,400,40,400,250));
  assert(!control::validMove(Dir::PivotLeft,40,251,40,400,250));
  assert(!control::validMove(Dir::Forward,41,100,40,400,250));
  assert(!control::validMove(Dir::Forward,30,uint32_t(-1),40,400,250));
  assert(!control::validMove(static_cast<Dir>(99),30,100,40,400,250));
  control::Lease lease;
  assert(lease.start(0xFFFFFFF0,40)); assert(!lease.start(10,400));
  assert(!lease.expired(0x10,120)); assert(lease.expired(0x18,120));
  lease.stop(); assert(lease.start(0,400)); assert(lease.expired(120,120));
  std::cout << "PASS policy: all edge combinations, gates, bounds, rollover, stale lease\n";

  levels[D1]=HIGH;
  assert(motionBegin()); stopped();
  assert(motionStart(Dir::Forward,30,400,fakeNow));
  assert(duty[D2]>0 && duty[D8]>0 && duty[D3]==0 && duty[D9]==0);
  assert(!motionStart(Dir::Forward,30,400,fakeNow));
  fakeNow=121; timerCallback(nullptr); stopped(); assert(motionTakeTrip());
  assert(motionStart(Dir::PivotLeft,30,100,fakeNow)); assert(duty[D2]==0 && duty[D8]>0);
  levels[D1]=LOW; timerCallback(nullptr); stopped(); assert(motionTakeTrip());
  levels[D1]=HIGH; fakeNow=0xFFFFFFF0;
  assert(motionStart(Dir::Forward,30,40,fakeNow)); fakeNow=0x18; timerCallback(nullptr); stopped();
  assert(!motionTakeTrip());
  assert(!motionStart(Dir::Forward,30,40,fakeNow-120));
  assert(motionStart(Dir::Forward,30,40,fakeNow));
  pwmWriteOk=false; motionStop(); stopped();
  for(int p:{D2,D3,D8,D9}) assert(levels[p]==LOW);
  assert(!motionReady()); assert(motionTakeTrip());
  pwmWriteOk=true; assert(!motionStart(Dir::Forward,30,40,fakeNow));
  std::cout << "PASS motor adapter: independent timer, bumper, PWM errors, no extension, sample age\n";

  assert(busBegin()); assert(pcfBegin()); assert(Wire.pcf==0xFF);
  Wire.nack=true; assert(!pcfSet(PCF_DRIVER,true));
  Wire.nack=false; assert(pcfSet(PCF_AMP,true));
  assert(Wire.pcf & PCF_DRIVER); // failed enable must never be replayed
  assert(!(Wire.pcf & PCF_AMP));
  assert(pcfReleaseAll());
  Wire.nack=true; assert(!pcfSet(PCF_AMP,false)); assert(pcfFaultActive());
  Wire.nack=false; assert(pcfReleaseAll());
  assert(!pcfSet(PCF_FAULT,true));
  std::cout << "PASS expander: NACK, repeat write, failure recovery, input protection\n";

  assert(sensorsBegin());
  float battery=0; assert(sensorsReadBattery(battery)); assert(battery>3.89f&&battery<3.91f);
  Wire.neverReady=true; uint32_t start=fakeNow; assert(!sensorsReadBattery(battery)); assert(fakeNow-start<=20); Wire.neverReady=false;
  Wire.shortRead=true; assert(!sensorsReadBattery(battery)); Wire.shortRead=false;
  Wire.battery=4.5f; assert(!sensorsReadBattery(battery));
  Wire.nack=true; assert(!sensorsReadBattery(battery));
  std::cout << "PASS battery ADC: NACK/short read, timeout, plausibility\n";
}
