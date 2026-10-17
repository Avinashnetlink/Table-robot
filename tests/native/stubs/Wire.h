#pragma once
#include <cstdint>
#include <vector>
#ifndef BOB_EDGE_SENSOR
#define BOB_EDGE_SENSOR 6180
#endif
struct FakeWire {
  uint8_t address=0, selected=1, pcf=0xFF, mux=0;
  uint16_t config=0, rangeRegister=0;
  bool nack=false, shortRead=false, neverReady=false, badMux=false, wrongModel=false, clearFail=false;
  int missingChannel=-1, writes=0;
  bool fresh[3]={true,true,true};
  uint16_t rangeMm[3]={30,30,30};
  uint8_t rangeStatus[3]={0,0,0};
  float battery=3.9f;
  std::vector<uint8_t> tx,rx;
  int channel() const { return mux==1 ? 0 : mux==2 ? 1 : mux==4 ? 2 : -1; }
  bool begin(int,int,uint32_t) { return true; }
  void setTimeOut(int) {}
  void beginTransmission(uint8_t addr) { address=addr; tx.clear(); }
  void write(uint8_t v) { tx.push_back(v); }
  uint8_t endTransmission(bool=true) {
    ++writes;
    if (nack) return 2;
    if (address==0x70 && tx.size()==1) mux=tx[0];
    if (address==0x20 && tx.size()==1) pcf=tx[0];
    if (address==0x29) {
      int ch=channel();
      if (ch<0 || ch==missingChannel) return 2;
#if BOB_EDGE_SENSOR == 6180
      if(tx.size()<2) return 2;
      rangeRegister=(uint16_t(tx[0])<<8)|tx[1];
      bool clear=tx.size()==3 && rangeRegister==0x15;
#else
      rangeRegister=tx[0];
      bool clear=tx.size()==2 && rangeRegister==0x0B;
#endif
      if(clear) { if(clearFail) return 2; fresh[ch]=false; }
    }
    if (address==0x48 && !tx.empty()) {
      selected=tx[0];
      if (tx.size()==3) config=(uint16_t(tx[1])<<8)|tx[2];
    }
    return 0;
  }
  uint8_t requestFrom(uint8_t addr,uint8_t count) {
    rx.clear();
    if (shortRead || nack) return 0;
    if (addr==0x70) rx={uint8_t(badMux ? 0 : mux)};
    if (addr==0x20) rx={pcf};
    if (addr==0x29) {
      int ch=channel(); if(ch<0 || ch==missingChannel) return 0;
#if BOB_EDGE_SENSOR == 6180
      if(rangeRegister==0) rx={uint8_t(wrongModel ? 0 : 0xB4)};
      else if(rangeRegister==0x4F) rx={uint8_t(fresh[ch] ? 4 : 0)};
      else if(rangeRegister==0x4D) rx={uint8_t(rangeStatus[ch]<<4)};
      else if(rangeRegister==0x62) rx={uint8_t(rangeMm[ch])};
#else
      if(rangeRegister==0xC0) rx={uint8_t(wrongModel ? 0 : 0xEE)};
      else if(rangeRegister==0x13) rx={uint8_t(fresh[ch] ? 4 : 0)};
      else if(rangeRegister==0x14) {
        rx.resize(12); rx[0]=rangeStatus[ch]<<3; rx[10]=rangeMm[ch]>>8; rx[11]=rangeMm[ch];
      }
#endif
    }
    if (addr==0x48) {
      uint16_t val=config;
      if (selected==1) { if (neverReady) val &= ~0x8000; else val|=0x8000; }
      else val=uint16_t(int16_t((battery/2)/.000125f));
      rx={uint8_t(val>>8),uint8_t(val)};
    }
    return uint8_t(rx.size()==count ? count : 0);
  }
  int read() { if(rx.empty()) return -1; auto v=rx.front();rx.erase(rx.begin());return v; }
};
extern FakeWire Wire;
