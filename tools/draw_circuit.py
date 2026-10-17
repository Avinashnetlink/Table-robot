#!/usr/bin/env python3
"""Generate the revision 3 electrical connection overview (PNG + editable SVG)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]
fig=plt.figure(figsize=(16,12),facecolor='#f4f7fb')
fig.text(.035,.958,'BOB / revision 3 wiring',fontsize=27,weight='bold',color='#172b42')
fig.text(.035,.93,'XIAO ESP32-S3 Sense · Three downward ToF modules + TCA9548A · Measurements and calibration pending',fontsize=12,color='#425b73')

def panel(rect,title):
 ax=fig.add_axes(rect);ax.set_xlim(0,100);ax.set_ylim(0,100);ax.axis('off')
 ax.add_patch(FancyBboxPatch((0,0),100,100,boxstyle='round,pad=0,rounding_size=2',fc='white',ec='#cfdae4'))
 ax.text(4,94,title,fontsize=14,weight='bold',color='#172b42',va='top')
 return ax

def box(ax,x,y,w,h,label,color='#eaf1f8',size=10):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.4,rounding_size=1',fc=color,ec='#8297ac'))
 ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=size,color='#172b42')

def wire(ax,pts,color='#ce5c48',label=None,xy=None):
 ax.plot(*zip(*pts),color=color,lw=1.8)
 if label: ax.text(*xy,label,fontsize=9,color=color,va='bottom',bbox=dict(fc='white',ec='none',pad=.5))

ax=panel([.035,.57,.58,.33],'01  Power distribution and physical motor isolation')
box(ax,4,55,18,19,'Protected 1S cell\n3.6 / 3.7 V nominal')
box(ax,28,58,12,13,'F1 fuse')
box(ax,47,58,13,13,'SW1\nmain')
wire(ax,[(22,65),(28,65)]);wire(ax,[(40,65),(47,65)]);wire(ax,[(60,65),(66,65),(66,80),(72,80)],label='VBAT',xy=(61,82))
box(ax,72,73,24,15,'XIAO BAT+')
wire(ax,[(66,65),(72,65)]);box(ax,72,56,24,15,'MAX98357A VIN\nC5 100µF + C6 100nF')
wire(ax,[(66,65),(66,41),(72,41)]);box(ax,72,34,24,15,'SW2 motor kill',color='#fff0e5')
wire(ax,[(84,34),(84,26)]);box(ax,72,10,24,16,'DRV8833 VM\nC1 1000µF + C2 100nF')
wire(ax,[(12,55),(12,26),(61,26)],'#425b73',label='Common GND: BAT− / logic / driver / amp',xy=(4,18))
ax.text(4,8,'3V3 → OLED, battery ADC, expander, mux, ToF carriers and logic pull-ups.',fontsize=10,color='#425b73')
ax.text(4,3,'Disconnect USB + cell for wiring. SW1 is not a motor kill with USB attached.',fontsize=9,color='#a33')

ax=panel([.635,.57,.33,.33],'02  XIAO pin map')
rows=[('D0 / GPIO1','Touch via 470Ω'),('D1 / GPIO2','Bumpers + 10k pull-up'),('D2,D3 / GPIO3,4','Left AIN1,AIN2'),('D4,D5 / GPIO5,6','SDA,SCL at 100 kHz'),('D6,D7 / GPIO43,44','Speaker BCLK,LRC'),('D8,D9 / GPIO7,8','Right BIN1,BIN2'),('D10 / GPIO9','Speaker DIN'),('GPIO42,41','Built-in PDM clock,data')]
for i,(pin,dest) in enumerate(rows):
 y=81-i*8;ax.text(4,y,pin,fontsize=10,weight='bold');ax.text(48,y,dest,fontsize=10)
ax.text(4,12,'Motor inputs: each 100k to GND.\nIsolate matching Sense J3 SD pull-ups.\nKeep microSD empty; keep mic J1/J2 intact.',fontsize=10,color='#425b73',va='center')

ax=panel([.035,.295,.45,.25],'03  Shared bus and battery measurement')
box(ax,4,58,24,22,'XIAO D4 / D5\nSDA / SCL',size=11)
wire(ax,[(28,69),(37,69),(37,80),(43,80)],'#207a9b')
wire(ax,[(37,69),(37,55),(43,55)],'#207a9b')
wire(ax,[(37,55),(37,30),(43,30)],'#207a9b')
box(ax,43,73,51,14,'SSD1306 0x3C · 3V3')
box(ax,43,48,51,14,'ADS1115 0x48 · battery A3 only')
box(ax,43,23,51,14,'PCF8574 0x20 · A0–A2 = GND')
ax.text(4,39,'100 kHz\n3.3 V pull-ups\ncommon GND',fontsize=11,color='#207a9b')
ax.text(4,10,'ADS A3 ← VBAT / 100k–100k divider + 100nF to GND\nADS A0, A1, A2 → GND (unused). Mux branch below.',fontsize=10,va='center')

ax=panel([.505,.295,.46,.25],'04  Motor and amplifier enables')
ax.text(4,80,'P1 → Q1 → amplifier SD       P2 → Q2 → driver nSLEEP',fontsize=10,weight='bold')
ax.text(4,65,'Each inverter: PCF → 100k → NPN base; emitter → GND\nPCF → 100k → 3V3; collector/enable → 22k → 3V3',fontsize=10,va='center')
ax.text(4,47,'PCF low = enabled. Released = disabled. Verify module straps.\nMCU reset retains PCF state; four motor pulldowns are required.',fontsize=10,color='#a33',va='center')
ax.text(4,30,'P3 ← nFAULT + 10k to 3V3. P0 and P4–P7 stay unused.\nSpeaker connects OUT+ ↔ OUT− only; neither wire to GND.',fontsize=10,va='center')
ax.text(4,12,'100nF across each motor. Bumpers: NO parallel → D1/GND.\nOptional NC series requires matching firmware polarity.',fontsize=10,color='#425b73',va='center')

ax=panel([.035,.055,.93,.215],'05  Three downward edge sensors — choose ONE family for all three')
box(ax,3,18,19,62,'TCA9548A · 0x70\nSDA D4 / SCL D5\nVCC 3V3 / GND\nA0/A1/A2 → GND\nRESET: 10k → 3V3\nCH3–7 unused',size=10)
for i,(label,y) in enumerate([('LEFT',72),('RIGHT',49),('CENTER',26)]):
 wire(ax,[(22,y),(37,y)],'#207a9b')
 box(ax,37,y-8,23,16,f'{label} · sensor 0x29',size=10)
 ax.text(30,y+2,f'SD{i}/SC{i}',fontsize=9,color='#207a9b')
ax.text(63,76,'3 × GY-6180 / VL6180X   OR   3 × VL53L0X',fontsize=11,weight='bold')
ax.text(63,65,'Each: VIN → 3V3*, GND common; SDA/ SCL → branch\nDo not join the three branches or mix sensor families.\nAll sensors face DOWN. Bumpers detect forward contact.\nValid desk distance required on all three before movement.',fontsize=10,va='top')
ax.text(63,30,'* Verify carrier regulator + host I²C compatibility.\nBare VL6180X is a 2.8 V device. No 5 V pull-ups.\nNo separate forward ToF or IR LED circuit.',fontsize=10,color='#a33',va='top')
ax.text(3,5,'Mounting trials: ~30 mm (VL6180X) / ~60 mm (VL53L0X). Calibrate desk bands and measure stopping margin before driving.',fontsize=10,color='#425b73')
fig.text(.035,.025,'See docs/HARDWARE.md for component values and power checks. Motion stays locked until calibration. No automatic cliff recovery.',fontsize=11,color='#425b73')
for ext in ('svg','png'):
 fig.savefig(ROOT/'images'/f'bob-wiring.{ext}',dpi=140,facecolor=fig.get_facecolor())
plt.close(fig)
