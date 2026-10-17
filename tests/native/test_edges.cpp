#include <cassert>
#include <iostream>
#include <Wire.h>
#include "bus.h"
#include "sensors.h"
#include "config.h"
uint32_t fakeNow=0;
FakeWire Wire;
static void fresh() { fakeNow+=50; for(auto &v:Wire.fresh) v=true; }
static bool supported(const EdgeReading &r) { return r.table[0]&&r.table[1]&&r.table[2]; }
int main() {
  assert(busBegin()); EdgeReading r;
  for(int i=0;i<3;++i) {
    Wire.rangeMm[i]=(EDGE_MIN_MM[i]+EDGE_MAX_MM[i])/2;
    Wire.rangeStatus[i]=BOB_EDGE_SENSOR==6180 ? 0 : 11;
  }
  Wire.wrongModel=true; assert(!edgesBegin()); Wire.wrongModel=false;
  Wire.missingChannel=1; assert(!edgesBegin()); Wire.missingChannel=-1;
  assert(edgesBegin()); assert(Wire.mux==0);
  fresh(); assert(!sensorsReadEdges(r)); // discard startup/retained frames
  fresh(); assert(sensorsReadEdges(r)); assert(!supported(r));
  auto sample=r.sampleAt;
  assert(sensorsReadEdges(r)); assert(!supported(r)); assert(r.sampleAt==sample); // no duplicate acquisition
  fresh(); assert(sensorsReadEdges(r)); assert(!supported(r));
  fresh(); assert(sensorsReadEdges(r)); assert(supported(r)); assert(Wire.mux==0);
  for(int i=0;i<3;++i) {
    auto save=Wire.rangeMm[i]; Wire.rangeMm[i]=EDGE_MAX_MM[i]+1;
    fresh(); assert(sensorsReadEdges(r)); assert(!r.table[i]); // immediate cliff
    Wire.rangeMm[i]=save;
    for(int n=0;n<3;++n) { fresh(); assert(sensorsReadEdges(r)); }
    assert(supported(r));
  }
  Wire.rangeMm[0]=EDGE_MIN_MM[0]-1; fresh(); assert(sensorsReadEdges(r)); assert(!r.table[0]);
  Wire.rangeMm[0]=(EDGE_MIN_MM[0]+EDGE_MAX_MM[0])/2;
  Wire.rangeStatus[1]=7; fresh(); assert(!sensorsReadEdges(r)); assert(!r.valid[1]);
  Wire.rangeStatus[1]=BOB_EDGE_SENSOR==6180 ? 0 : 11;
  Wire.badMux=true; fresh(); assert(!sensorsReadEdges(r)); Wire.badMux=false;
  Wire.shortRead=true; fresh(); assert(!sensorsReadEdges(r)); Wire.shortRead=false;
  Wire.clearFail=true; fresh(); assert(!sensorsReadEdges(r)); Wire.clearFail=false;
  Wire.missingChannel=2; fresh(); assert(!sensorsReadEdges(r)); Wire.missingChannel=-1;
  for(int n=0;n<4;++n) { fresh(); sensorsReadEdges(r); } // discard stale latched frame, then acquire three new frames
  assert(supported(r));
  fakeNow+=SENSOR_MAX_AGE_MS; assert(!sensorsReadEdges(r)); assert(!supported(r));
  fresh(); assert(!sensorsReadEdges(r)); // old latched frame isn't fresh just because it was read now
  fresh(); assert(sensorsReadEdges(r)); assert(!supported(r));
  fresh(); assert(sensorsReadEdges(r)); assert(!supported(r));
  fresh(); assert(sensorsReadEdges(r)); assert(supported(r));
  fakeNow=0xFFFFFD00; assert(edgesBegin());
  fresh(); assert(!sensorsReadEdges(r));
  for(int n=0;n<3;++n) { fresh(); assert(sensorsReadEdges(r)); }
  assert(supported(r));
  edgesEnd(); assert(Wire.mux==0); assert(!sensorsReadEdges(r));
  std::cout << "PASS three " << edgeSensorName() << " edges: identity, mux, distinct samples, cliff, invalid/stale, bus faults, rollover, sleep\n";
}
