#!/usr/bin/env python3
"""Generate the revision 3.1 module circuit sheets (PNG + editable SVG)."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams['svg.fonttype']='none'
plt.rcParams['svg.hashsalt']='bob-circuit-r3.1'
ROOT=Path(__file__).resolve().parents[1]
fig=plt.figure(figsize=(16,12),facecolor='#f4f7fb')
fig.text(.035,.958,'BOB / revision 3.1 wiring',fontsize=27,weight='bold',color='#172b42')
fig.text(.035,.93,'XIAO ESP32-S3 Sense · Three downward VL53L0X modules + TCA9548A · Measurements and calibration pending',fontsize=12,color='#425b73')

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

ax=panel([.035,.055,.93,.215],'05  Selected edge sensors — three Robu VL53L0X modules, all facing down')
box(ax,3,18,19,62,'TCA9548A · 0x70\nSDA D4 / SCL D5\nVCC 3V3 / GND\nA0/A1/A2 → GND\nRESET: 10k → 3V3\nCH3–7 unused',size=10)
for i,(label,y) in enumerate([('LEFT',72),('RIGHT',49),('CENTER',26)]):
 wire(ax,[(22,y),(37,y)],'#207a9b')
 box(ax,37,y-8,23,16,f'{label} · sensor 0x29',size=10)
 ax.text(30,y+2,f'SD{i}/SC{i}',fontsize=9,color='#207a9b')
ax.text(63,76,'3 × VL53L0X  |  firmware default = 530',fontsize=11,weight='bold')
ax.text(63,65,'Each: VIN → 3V3*, GND common; SDA/ SCL → branch\nDo not join the three SDA/SCL branches.\nAll sensors face DOWN. Bumpers detect forward contact.\nValid desk distance required on all three before movement.',fontsize=10,va='top')
ax.text(63,30,'* Verify carrier regulator + host I²C compatibility.\nXSHUT: carrier pull-up to sensor rail; GPIO1 unused.\nNo separate forward ToF or IR LED circuit.',fontsize=10,color='#a33',va='top')
ax.text(3,5,'Mounting trial: ~60 mm (VL53L0X). Calibrate desk bands and measure stopping margin before driving.',fontsize=10,color='#425b73')
fig.text(.035,.025,'Full pin-level sheets: bob-circuit-1/2/3.png + docs/CIRCUIT.md. Motion stays locked until calibration. No automatic cliff recovery.',fontsize=11,color='#425b73')
for ext in ('svg','png'):
 fig.savefig(ROOT/'images'/f'bob-wiring.{ext}',dpi=140,facecolor=fig.get_facecolor())
plt.close(fig)

# Detailed module-level schematics. Equal net names join across panels/sheets.
from matplotlib.patches import Rectangle
INK='#172b42'; NET='#207a9b'; RED='#aa4534'
plt.rcParams['svg.fonttype']='none'

def sheet(num, title):
 global fig
 fig=plt.figure(figsize=(18,13),facecolor='#f4f7fb')
 fig.text(.035,.962,f'BOB / {title}',fontsize=25,weight='bold',color=INK)
 fig.text(.035,.935,f'Circuit {num}/3 · Revision 3.1 · XIAO ESP32-S3 Sense + 3 × Robu VL53L0X · Module wiring, not physical header order',fontsize=12,color=INK)
 fig.text(.035,.022,'Same net label = connected. Dots = junctions. NC = no wire. All GNDs common. See docs/CIRCUIT.md for carrier checks and assembly.',fontsize=11,color=INK)

def save(num):
 for ext in ('png','svg'):
  fig.savefig(ROOT/'images'/f'bob-circuit-{num}.{ext}',dpi=150,facecolor=fig.get_facecolor())
 plt.close(fig)

def t(ax,x,y,txt,size=10,color=INK,**kw):
 ax.text(x,y,txt,fontsize=size,color=color,va='center',**kw)

def line(ax,pts,color=NET):
 ax.plot(*zip(*pts),color=color,lw=1.5)

def dot(ax,x,y):
 ax.plot(x,y,'o',color=NET,ms=3)

def res(ax,x,y,label,vertical=False,length=12):
 if vertical:
  line(ax,[(x,y),(x,y-length*.25)])
  ax.add_patch(Rectangle((x-1,y-length*.75),2,length*.5,ec=INK,fc='white',lw=1.3))
  line(ax,[(x,y-length*.75),(x,y-length)])
  t(ax,x+2,y-length/2,label,9)
 else:
  line(ax,[(x,y),(x+length*.25,y)])
  ax.add_patch(Rectangle((x+length*.25,y-1),length*.5,2,ec=INK,fc='white',lw=1.3))
  line(ax,[(x+length*.75,y),(x+length,y)])
  t(ax,x+length/2,y+4,label,9,ha='center')

def cap(ax,x,y,label,length=14):
 line(ax,[(x,y),(x,y-length*.43)])
 line(ax,[(x-2,y-length*.43),(x+2,y-length*.43)],INK)
 line(ax,[(x-2,y-length*.57),(x+2,y-length*.57)],INK)
 line(ax,[(x,y-length*.57),(x,y-length)])
 t(ax,x+3,y-length/2,label,9)

def device(ax,x,y,w,h,title,left,right):
 # Entries are (printed pin, external net); each terminal has its own stub.
 ax.add_patch(Rectangle((x,y),w,h,ec=INK,fc='#edf3fa',lw=1.5))
 t(ax,x+w/2,y+h-5,title,11,ha='center',weight='bold')
 for entries,side in ((left,'left'),(right,'right')):
  step=(h-16)/max(1,len(entries))
  for i,(pin,net) in enumerate(entries):
   yy=y+h-15-i*step
   if side=='left':
    line(ax,[(x-5,yy),(x,yy)])
    t(ax,x+1.5,yy,pin,9)
    t(ax,x-6,yy,net,9,NET,ha='right')
   else:
    line(ax,[(x+w,yy),(x+w+5,yy)])
    t(ax,x+w-1.5,yy,pin,9,ha='right')
    t(ax,x+w+6,yy,net,9,NET)

def note(ax,txt,y=5,color=INK,size=10):
 t(ax,4,y,txt,size,color)

sheet(1,'power, controller and battery sensing')
a=panel([.035,.65,.93,.26],'01  Protected 1S cell and power rails')
box(a,3,54,14,22,'1S protected cell\n3.6/3.7 V nominal')
line(a,[(17,69),(22,69)]);box(a,22,63,10,12,'F1')
line(a,[(32,69),(37,69)]);box(a,37,63,11,12,'SW1')
line(a,[(48,69),(55,69),(55,80),(61,80)])
dot(a,55,69);t(a,51,74,'VBAT',10,RED)
box(a,61,74,13,12,'XIAO BAT+')
line(a,[(55,69),(55,51),(61,51)]);box(a,61,44,13,14,'SW2 kill')
line(a,[(74,51),(82,51)]);box(a,82,44,14,14,'VM / driver')
line(a,[(55,51),(55,29),(61,29)]);dot(a,55,51)
box(a,61,22,35,14,'VBAT → amplifier VIN + battery R1')
line(a,[(10,54),(10,29),(47,29)])
t(a,12,34,'GND → XIAO BAT− / all module GNDs',10)
t(a,3,12,'XIAO 3V3 → logic modules + three compatible sensor VIN inputs. C7 10µF || C8 100nF: 3V3 to GND.',11)
t(a,3,5,'XIAO 5V: no external connection. Disconnect USB and cell to wire. SW1 does not isolate USB power.',10,RED)

a=panel([.035,.075,.44,.55],'02  XIAO external header and onboard devices')
device(a,31,32,39,55,'XIAO ESP32-S3 Sense',
 [('D0 / 1','TOUCH'),('D1 / 2','BUMPER'),('D2 / 3','AIN1'),('D3 / 4','AIN2'),('D4 / 5','SDA'),('D5 / 6','SCL')],
 [('D6 / 43','BCLK'),('D7 / 44','LRC'),('D8 / 7','BIN1'),('D9 / 8','BIN2'),('D10 / 9','DIN')])
t(a,4,26,'Mic PDM CLK / DATA = GPIO42 / 41; retain J1/J2.',10)
t(a,4,21,'Camera: ribbon connector; no external jumpers.',10)
t(a,4,16,'XCLK/PCLK/VSYNC/HREF = 10 / 13 / 38 / 47',10)
t(a,4,11,'SCCB SDA/SCL = 40 / 39; D0–D7 =',10)
t(a,4,7,'15 / 17 / 18 / 16 / 14 / 12 / 11 / 48',10)
t(a,4,2.5,'D8–D10: isolate Sense SD pull-ups; remove SD card.',10,RED)

a=panel([.495,.36,.47,.265],'03  Battery divider / ADS1115 A3')
t(a,5,74,'VBAT',11,NET);line(a,[(17,74),(23,74)])
res(a,23,74,'R1 100k',length=20);line(a,[(43,74),(51,74),(51,61)])
dot(a,51,74);line(a,[(51,74),(69,74)]);t(a,70,74,'BAT_SENSE → A3',10,NET)
res(a,51,61,'R2 100k',True,24);line(a,[(51,37),(51,23)])
line(a,[(51,61),(28,61)]);dot(a,51,61);cap(a,28,61,'C9 100nF',38)
line(a,[(28,23),(51,23)]);t(a,51,16,'GND',10,NET,ha='center')
t(a,4,6,'A3 ≈ 2.1 V at full charge. ADS VDD=3V3; A0/A1/A2 + ADDR=GND.',10)

a=panel([.495,.075,.47,.265],'04  Touch and two parallel NO bumpers')
t(a,4,77,'D0',10,NET);line(a,[(10,77),(18,77)]);res(a,18,77,'R13 470Ω',length=18)
line(a,[(36,77),(45,77)]);box(a,45,70,48,13,'Insulated copper touch pad')
t(a,4,51,'D1 / BUMPER',10,NET);line(a,[(25,51),(92,51)])
for x in (32,56,78,92): dot(a,x,51)
res(a,32,51,'R14 10k',True,19);t(a,32,25,'3V3',9,NET,ha='center')
cap(a,56,51,'C14 100nF',19);t(a,56,25,'GND',9,NET,ha='center')
for x,label in ((78,'Left NO'),(92,'Right NO')):
 line(a,[(x,51),(x,43)]);dot(a,x,43)
 line(a,[(x,27),(x,33),(x-3,41)]);dot(a,x,33)
 t(a,x,22,'GND',8,NET,ha='center');t(a,x,56,label,8,ha='center')
t(a,4,13,'Each switch: COM → GND, NO → BUMPER, NC unused.',10)
t(a,4,5,'Default: BUMPER_NC_SERIES=false. Pressing either pulls D1 low.',10)
save(1)

sheet(2,'I²C bus and three downward VL53L0X modules')
a=panel([.035,.56,.93,.35],'05  Shared upstream bus / 100 kHz / 3V3 logic')
t(a,3,81,'SDA = D4 / GPIO5        SCL = D5 / GPIO6',12,NET,weight='bold')
t(a,3,72,'Optional R23 4.7k: SDA → 3V3; R24 4.7k: SCL → 3V3. Account for existing carrier pull-ups.',11)
# Explicit per-device pin lists are clearer than crossing shared bus lines.
for x,title,rows in [
 (3,'OLED / 0x3C',['VCC → 3V3','GND → GND','SDA → SDA','SCL → SCL','4-pin SSD1306']),
 (26,'ADS1115 / 0x48',['VDD → 3V3; GND → GND','SDA → SDA; SCL → SCL','ADDR, A0,A1,A2 → GND','A3 → BAT_SENSE (sheet 1)','ALERT/RDY → NC']),
 (51,'PCF8574 / 0x20',['VCC → 3V3; GND → GND','SDA → SDA; SCL → SCL','A0,A1,A2 → GND; INT → NC','P1 → AMP_CTL; P2 → DRV_CTL','P3 → FAULT; P0,P4–P7 → NC']),
 (77,'Mux / 0x70',['VCC → 3V3; GND → GND','SDA → SDA; SCL → SCL','A0,A1,A2 → GND','RESET → R25 10k → 3V3','CH3–7 → NC'])]:
  width=21 if x in (3,77) else 23
  box(a,x,21,width,41,'',size=10)
  t(a,x+width/2,55,title,11,ha='center',weight='bold')
  for i,row in enumerate(rows):t(a,x+1,47-i*5.5,row,9)
note(a,'PCF8574A alternative = 0x38: update PCF_ADDR. Driver fault pull-up R21 is on sheet 3. R25 only if missing on carrier.',10)

a=panel([.035,.075,.93,.46],'06  TCA9548A branch wiring — never join the three branches')
box(a,4,25,16,58,'TCA9548A\n\n0x70\n\nUpstream:\nSDA / SCL',size=12)
for i,(label,y,vio,vlogic) in enumerate([('LEFT',78,'VIO_L','VLOGIC_L'),('RIGHT',55,'VIO_R','VLOGIC_R'),('CENTER',32,'VIO_C','VLOGIC_C')]):
 # Separate, individually labelled SDA and SCL wires.
 line(a,[(20,y),(36,y)]);line(a,[(20,y-6),(36,y-6)])
 t(a,22,y+2.5,f'SD{i} → SDA',9,NET);t(a,22,y-8.5,f'SC{i} → SCL',9,NET)
 box(a,36,y-12,18,17,f'{label} VL53L0X\n0x29 · faces down',size=11)
 t(a,57,y-1,f'VIN/VCC → 3V3*; GND → GND; GPIO1 → NC',10)
 t(a,57,y-7,f'XSHUT → onboard pull-up or R{32+i} 10k → {vlogic}*',10)
 t(a,57,y-13,f'Optional R{26+2*i}/R{27+2*i}: SDA/SCL → {vio}* (4.7k start)',9)
note(a,'* 3V3 must feed a compatible carrier input. VIO = verified bus pull-up rail; VLOGIC = actual sensor logic rail (often 2.8 V).',16,size=10)
note(a,'Level-shifted SDA/SCL does not imply level-shifted XSHUT. Keep correct carrier pull-ups; never float XSHUT or apply 5 V.',10,color=RED,size=10)
note(a,'Use printed pin names, not assumed header order. Mount ~60 mm above desk, calibrate each sensor; firmware defaults to 530.',4,size=10)
save(2)

sheet(3,'motor driver, speaker and enable inverters')
a=panel([.035,.49,.45,.42],'07  DRV8833 carrier and two motors')
device(a,31,28,37,56,'DRV8833',
 [('VM','VM'),('GND','GND'),('AIN1','D2 / AIN1'),('AIN2','D3 / AIN2'),('BIN1','D8 / BIN1'),('BIN2','D9 / BIN2')],
 [('AOUT1','LEFT +'),('AOUT2','LEFT −'),('BOUT1','RIGHT +'),('BOUT2','RIGHT −'),('nSLEEP','DRIVER_EN'),('nFAULT','FAULT')])
t(a,4,23,'R3/R4/R5/R6: 100k from AIN1/AIN2/BIN1/BIN2 to GND.',10)
t(a,4,18,'C1 1000µF (+ to VM) || C2 100nF: VM → GND.',10)
t(a,4,13,'C3/C4 100nF: across left/right motor tabs respectively.',10)
t(a,4,8,'FAULT → PCF P3; R21 10k from FAULT to 3V3.',10)
t(a,4,3,'Retain onboard sense/charge-pump parts; encoders NC.',10)

a=panel([.505,.49,.46,.42],'08  MAX98357A carrier and speaker')
device(a,31,28,37,56,'MAX98357A',
 [('VIN','VBAT'),('GND','GND'),('BCLK','D6 / BCLK'),('LRC','D7 / LRC'),('DIN','D10 / DIN')],
 [('SD_MODE','AMP_EN'),('GAIN','R22 → VBAT'),('OUT+','SPEAKER +'),('OUT−','SPEAKER −')])
t(a,4,23,'R22 = 100k from GAIN to VIN/VBAT; check carrier straps.',10)
t(a,4,18,'C5 100µF (+ to VBAT) || C6 100nF: VIN → GND.',10)
t(a,4,13,'Use A version (I²S). Measure speaker power and heating.',10)
t(a,4,8,'Speaker is between OUT+ and OUT− only.',11,RED,weight='bold')
t(a,4,3,'Neither speaker wire connects to GND.',10,RED)

for rect,title,pin,pull,base,collector,q,enable in [
 ([.035,.075,.45,.39],'09  Amplifier enable inverter','P1 / AMP_CTL','R15','R16','R17','Q1','AMP_EN'),
 ([.505,.075,.46,.39],'10  Driver enable inverter','P2 / DRV_CTL','R18','R19','R20','Q2','DRIVER_EN')]:
 a=panel(rect,title)
 t(a,4,55,pin,10,NET);line(a,[(25,55),(33,55)])
 dot(a,33,55);res(a,33,80,pull+' 100k',True,25);t(a,33,85,'3V3',10,NET,ha='center')
 res(a,33,55,base+' 100k',length=22);line(a,[(55,55),(60,55)])
 # NPN symbol, emitter arrow outward.
 line(a,[(60,47),(60,63)],INK)
 line(a,[(60,59),(70,68)],INK);line(a,[(60,51),(70,42)],INK)
 a.annotate('',xy=(69,43),xytext=(64,48),arrowprops=dict(arrowstyle='-|>',color=INK,lw=1.3))
 t(a,54,45,'B',9);t(a,72,65,'C',9);t(a,72,42,'E',9)
 line(a,[(70,42),(70,34)]);t(a,70,29,'GND',10,NET,ha='center')
 res(a,70,85,collector+' 22k',True,17);t(a,68,89,'3V3',10,NET,ha='right')
 dot(a,70,68);line(a,[(70,68),(93,68)]);t(a,78,73,enable,10,NET)
 t(a,7,35,q+' BC547 NPN',11,weight='bold')
 t(a,4,20,'PCF released/high → NPN ON → enable LOW → device OFF',10)
 t(a,4,14,'PCF low → NPN OFF → enable HIGH → device ON',10)
 t(a,4,8,'Remove conflicting carrier straps; verify actual B/C/E pinout.',10,RED)
 t(a,4,3,'Measure both logic levels before connecting motor power.',10,RED)
save(3)

# Keep generated vector files diff-friendly.
for svg in (ROOT/'images').glob('bob-*.svg'):
 svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
