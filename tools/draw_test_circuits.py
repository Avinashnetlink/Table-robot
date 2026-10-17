#!/usr/bin/env python3
"""Generate a local pin-level PNG/SVG for every hardware test (Matplotlib)."""
from pathlib import Path
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Arc
ROOT=Path(__file__).resolve().parents[1]
TESTS=ROOT/'code/tests'
plt.rcParams.update({'svg.fonttype':'none','svg.hashsalt':'bob-hardware-tests','font.family':'DejaVu Sans'})
INK='#243342';BLUE='#137cb2';CYAN='#00a4b9';RED='#ce343e';ORANGE='#df7900';GREEN='#24883b';GRAY='#606870';PURPLE='#8458b4'
fig=ax=None
wires=[]

def start(title,subtitle,w=1600,h=1100):
 global fig,ax,wires,W,H
 W,H=w,h;wires=[]
 fig,ax=plt.subplots(figsize=(w/100,h/100));fig.subplots_adjust(0,0,1,1)
 ax.set(xlim=(0,w),ylim=(h,0),aspect='equal');ax.axis('off')
 text(w/2,35,title,22,ha='center',bold=True)
 text(w/2,77,subtitle,11,ha='center')
 text(w/2,h-25,'Same named power/ground = same wire. Dot = joined. Bridge = crossing only. Pin names, not physical header order.',10,ha='center')

def text(x,y,s,size=12,ha='left',color=INK,bold=False):
 ax.text(x,y,s,fontsize=size,ha=ha,va='center',color=color,weight='bold' if bold else 'normal',zorder=10)

def wire(net,pts,color=GRAY,dashed=False):
 ax.plot(*zip(*pts),c=color,lw=1.8,ls='--' if dashed else '-',zorder=2)
 if not dashed:
  for a,b in zip(pts,pts[1:]):
   assert a[0]==b[0] or a[1]==b[1]
   wires.append((net,a,b,color))

def dot(x,y):ax.add_patch(Circle((x,y),4,fc=GRAY,zorder=8))
def flag(x,y,s='3V3',color=ORANGE):
 ax.text(x,y,s,fontsize=11,ha='center',va='center',color='white',weight='bold',zorder=10,bbox=dict(fc=color,ec=color,boxstyle='round,pad=.16'))
def gnd(x,y):
 for off,ww in ((0,30),(7,20),(14,9)):ax.plot([x-ww/2,x+ww/2],[y+off,y+off],c=GRAY,lw=1.8,zorder=5)
def power_pin(p,net='3V3',color=ORANGE):
 x,y=p;wire(net,[(x,y),(x,y-30)],color);flag(x,y-40,net,color)
def ground_pin(p):
 x,y=p;wire('GND',[(x,y),(x,y+30)]);gnd(x,y+30)

def mod(title,x,y,w,h,left=(),right=(),top=(),bottom=(),tint='#eef4fa'):
 ax.add_patch(Rectangle((x,y),w,h,fc=tint,ec=INK,lw=1.6,zorder=3))
 text(x+w/2,y+30,title,14,ha='center',bold=True)
 p={}
 for side,items in (('l',left),('r',right)):
  for name,dy in items:
   xx=x if side=='l' else x+w;yy=y+dy;p[name]=(xx,yy)
   text(xx+(10 if side=='l' else -10),yy,name,10,ha='left' if side=='l' else 'right')
 for side,items in (('t',top),('b',bottom)):
  for name,dx in items:
   xx=x+dx;yy=y if side=='t' else y+h;p[name]=(xx,yy)
   text(xx-10 if side=='t' else xx,yy-13,name,10,ha='right' if side=='t' else 'center')
 return p

def resistor(ref,value,a,b,optional=False,side=1):
 x,y=a;xx,yy=b;dx,dy=xx-x,yy-y
 import math
 length=math.hypot(dx,dy);px,py=-dy/length,dx/length
 shape=[(x+dx*t+px*v,y+dy*t+py*v) for t,v in ((0,0),(.2,0),(.3,6),(.4,-6),(.5,6),(.6,-6),(.7,6),(.8,0),(1,0))]
 ax.plot(*zip(*shape),c=GRAY,lw=1.7,zorder=5)
 label=f'{ref}{"*" if optional else ""}\n{value}'
 if x==xx:text(x+side*19,(y+yy)/2,label,10,ha='left' if side==1 else 'right')
 else:text((x+xx)/2,y-26,label,10,ha='center')

def cap(ref,value,x,y1,y2,polar=False,side=1):
 mid=(y1+y2)/2
 ax.plot([x,x],[y1,mid-5],c=GRAY,lw=1.7,zorder=5);ax.plot([x,x],[mid+5,y2],c=GRAY,lw=1.7,zorder=5)
 for yy in (mid-5,mid+5):ax.plot([x-15,x+15],[yy,yy],c=GRAY,lw=2,zorder=5)
 text(x+side*22,mid,f'{ref}\n{value}',10,ha='left' if side==1 else 'right')
 if polar:text(x-22,mid-17,'+',12,color=RED)

def nc(p):
 x,y=p
 ax.plot([x-5,x+5],[y-5,y+5],c=GRAY,lw=1.4,zorder=6);ax.plot([x-5,x+5],[y+5,y-5],c=GRAY,lw=1.4,zorder=6)

def board(right,height=500,x=90,y=180):
 p=mod('XIAO ESP32-S3 Sense',x,y,330,height,right=right,top=[('3V3',95)],bottom=[('GND',95)],tint='#e9f2ff')
 power_pin(p['3V3']);ground_pin(p['GND'])
 text(x+165,y+75,'USB-C data cable\nSerial: 115200 baud',11,ha='center')
 return p

def pullups(x,y,sda_y,scl_y):
 for ref,xx,net,target,col in [('R23',x,'SDA',sda_y,BLUE),('R24',x+95,'SCL',scl_y,CYAN)]:
  power_pin((xx,y));resistor(ref,'4.7k',(xx,y),(xx,y+65),True)
  wire(net,[(xx,y+65),(xx,target)],col);dot(xx,target)

def simple_oled(x,y):
 p=mod('SSD1306 • 0x3C',x,y,290,230,left=[('SDA',95),('SCL',155)],top=[('VCC',190)],bottom=[('GND',190)])
 power_pin(p['VCC']);ground_pin(p['GND']);return p

def touch(p,x,y):
 sx,sy=p;wire('TOUCH',[(sx,sy),(x-120,sy),(x-120,y),(x-85,y)],ORANGE)
 resistor('R13','470Ω',(x-85,y),(x,y))
 wire('PAD',[(x,y),(x+50,y)],ORANGE)
 ax.add_patch(Rectangle((x+50,y-45),220,90,fc='#faead3',ec=ORANGE,lw=1.5,zorder=3))
 text(x+160,y,'Insulated copper pad\n20 × 30 mm',12,ha='center')

def battery(x,y,ammeter=False):
 # Positive path exits as VBAT; use XIAO BAT+/BAT- board markings.
 for yy,ww in ((y+75,58),(y+105,32)):ax.plot([x-ww/2,x+ww/2],[yy,yy],c=GRAY,lw=2.5,zorder=5)
 wire('CELL+',[(x,y),(x,y+75)],RED);wire('GND',[(x,y+105),(x,y+185)]);gnd(x,y+185)
 text(x-45,y+88,'Protected\n1S cell',11,ha='right');text(x-30,y+50,'+',12,color=RED)
 wire('CELL+',[(x,y),(x+45,y)],RED)
 ax.add_patch(Rectangle((x+45,y-10),55,20,fc='white',ec=RED,lw=1.5,zorder=4));text(x+73,y-32,'F1 fuse',10,ha='center')
 wire('FUSED+',[(x+100,y),(x+135,y)],RED)
 ax.plot([x+135,x+190],[y,y-25],c=RED,lw=2,zorder=5)
 for xx in (x+135,x+200):ax.add_patch(Circle((xx,y),4,fc='white',ec=RED,lw=1.5,zorder=5))
 text(x+167,y-52,'SW1 main',10,ha='center')
 end=x+240;wire('VBAT',[(x+200,y),(end,y)],RED)
 if ammeter:
  ax.add_patch(Circle((end+25,y),25,fc='white',ec=INK,lw=1.6,zorder=5));text(end+25,y,'mA',11,ha='center')
  wire('VBAT',[(end+50,y),(end+90,y)],RED);end+=90
 flag(end,y,'VBAT',RED)
 return end,y

def inverter(x,y,idx,control):
 # Control input at x,y; output at x+220,y-45.
 rpull,rbase,rout=('R15','R16','R17') if idx==1 else ('R18','R19','R20')
 wire(control,[(x,y),(x+65,y)])
 resistor(rbase,'100k',(x+65,y),(x+145,y));wire(f'Q{idx}_B',[(x+145,y),(x+180,y)])
 resistor(rpull,'100k',(x+25,y),(x+25,y+75),side=-1);dot(x+25,y)
 wire('3V3',[(x+25,y+75),(x+25,y+105)],ORANGE);flag(x+25,y+118)
 ax.plot([x+180,x+180],[y-22,y+22],c=GRAY,lw=2,zorder=5)
 ax.plot([x+180,x+220],[y-12,y-45],c=GRAY,lw=2,zorder=5)
 ax.plot([x+180,x+220],[y+12,y+45],c=GRAY,lw=2,zorder=5)
 ax.annotate('',xy=(x+215,y+40),xytext=(x+195,y+23),arrowprops=dict(arrowstyle='-|>',color=GRAY,lw=1.5),zorder=6)
 wire('GND',[(x+220,y+45),(x+220,y+85)]);gnd(x+220,y+85)
 text(x+238,y+5,f'Q{idx}\nBC547',11)
 resistor(rout,'22k',(x+220,y-145),(x+220,y-45),side=-1)
 power_pin((x+220,y-145));dot(x+220,y-45)
 text(x+170,y+25,'B',9,ha='right');text(x+222,y-53,'C',9);text(x+224,y+53,'E',9)
 return x+220,y-45

def pcf(x,y,used):
 items=[('SDA',95),('SCL',150)]
 for i,name in enumerate(used):items.append((name,215+i*55))
 h=max(370,280+55*len(used))
 p=mod('PCF8574 • 0x20',x,y,290,h,left=items[:2],right=items[2:],top=[('VCC',140)],bottom=[('A0',45),('A1',105),('A2',165),('GND',235)])
 power_pin(p['VCC'])
 for n in ('A0','A1','A2','GND'):
  xx,yy=p[n];wire('GND',[(xx,yy),(xx,yy+35)]);dot(xx,yy+35)
 wire('GND',[(x+45,y+h+35),(x+235,y+h+35)]);gnd(x+140,y+h+65);wire('GND',[(x+140,y+h+35),(x+140,y+h+65)])
 text(x+145,y+h-55,'Unused P pins: NC\nINT: NC',10,ha='center')
 return p

def save(folder):
 # Draw bridges for different nets. Same-net intersections are junctions.
 seen=set()
 for i,(n,a,b,col) in enumerate(wires):
  for n2,c,d,col2 in wires[i+1:]:
   if (a[1]==b[1])==(c[1]==d[1]):continue
   h1,h2,v1,v2,hn,vn,hcol=(a,b,c,d,n,n2,col) if a[1]==b[1] else (c,d,a,b,n2,n,col2)
   xx,yy=v1[0],h1[1]
   if min(h1[0],h2[0])<=xx<=max(h1[0],h2[0]) and min(v1[1],v2[1])<=yy<=max(v1[1],v2[1]):
    if hn==vn:dot(xx,yy)
    elif min(h1[0],h2[0])<xx<max(h1[0],h2[0]) and min(v1[1],v2[1])<yy<max(v1[1],v2[1]) and (xx,yy) not in seen:
     seen.add((xx,yy));ax.plot([xx-8,xx+8],[yy,yy],c='white',lw=5,zorder=7)
     ax.add_patch(Arc((xx,yy),16,16,theta1=180,theta2=360,ec='white',lw=5,zorder=7))
     ax.add_patch(Arc((xx,yy),16,16,theta1=180,theta2=360,ec=hcol,lw=1.8,zorder=8))
 for ext in ('png','svg'):
  p=TESTS/folder/f'circuit.{ext}'
  fig.savefig(p,dpi=140,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
  if ext=='svg':p.write_text('\n'.join(l.rstrip() for l in p.read_text().splitlines())+'\n')
 plt.close(fig)

# T01/T02: traces inside the fitted Sense assembly, not loose wiring.
for folder,num,title,pairs in [
 ('T01_camera','T01','Camera', [('GPIO10','XCLK'),('GPIO13','PCLK'),('GPIO38','VSYNC'),('GPIO47','HREF'),('GPIO40','SCCB SDA'),('GPIO39','SCCB SCL')]),
 ('T02_microphone','T02','Built-in PDM microphone',[('GPIO42','CLK'),('GPIO41','DATA')])]:
 start(f'{num} — {title}', 'USB powers the XIAO. Dashed lines are existing Sense-board traces: do not add jumper wires.',1500,900)
 pp=board([(a,150+55*i) for i,(a,b) in enumerate(pairs)],height=560,x=120,y=180)
 qq=mod('Sense camera connector' if num=='T01' else 'Sense PDM microphone',880,250,440,440,left=[(b,80+55*i) for i,(a,b) in enumerate(pairs)],tint='#f2f7ed')
 for i,(a,b) in enumerate(pairs):
  x,y=pp[a];xx,yy=qq[b];wire(a,[(x,y),(650+i*20,y),(650+i*20,yy),(xx,yy)],BLUE,dashed=True)
 text(800,760,'Camera D0–D7 (onboard): GPIO15,17,18,16,14,12,11,48. Fit the camera ribbon + antenna.' if num=='T01' else 'Keep Sense microphone jumpers J1/J2 intact. No external microphone, resistor or amplifier is needed.',12,ha='center')
 text(800,808,'No battery or motor circuit is required for this individual test.',12,ha='center')
 save(folder)

# T04 OLED.
start('T04 — OLED display','Only XIAO + SSD1306 required. USB power; leave unrelated modules disconnected.',1500,900)
p=board([('D4 / GPIO5',210),('D5 / GPIO6',270)],height=420,y=220)
q=simple_oled(980,335)
wire('SDA',[p['D4 / GPIO5'],q['SDA']],BLUE);wire('SCL',[p['D5 / GPIO6'],q['SCL']],CYAN)
pullups(680,245,430,490)
text(760,760,'R23/R24*: add only if suitable pull-ups are absent on the OLED. Use 3.3 V, address 0x3C.',12,ha='center');save('T04_oled')

# T05 touch.
start('T05 — Touch-pad calibration','USB power. R13 is in series, close to D0. No external touch-controller module.',1450,800)
p=board([('D0 / GPIO1',190)],height=340,y=200);touch(p['D0 / GPIO1'],850,390)
text(760,650,'Foil must not touch GND, the antenna or exposed metal. Repeat calibration after mounting.',12,ha='center');save('T05_touch')

# T06 battery + ADC.
start('T06 — Battery voltage / ADS1115','Motor/amp not required. Use a protected 1S cell; verify BAT pad markings.',1700,1150)
p=board([('D4 / GPIO5',160),('D5 / GPIO6',220),('BAT+',360),('BAT−',420)],height=490,x=90,y=250)
q=mod('ADS1115 • 0x48',1000,315,320,460,left=[('SDA',95),('SCL',155),('A3',260)],top=[('VDD',180)],bottom=[('A0',40),('A1',100),('A2',160),('ADDR',220),('GND',280)],right=[('ALERT / RDY',330)])
power_pin(q['VDD']);nc(q['ALERT / RDY'])
wire('SDA',[p['D4 / GPIO5'],q['SDA']],BLUE);wire('SCL',[p['D5 / GPIO6'],q['SCL']],CYAN)
pullups(675,220,410,470)
for name in ('A0','A1','A2','ADDR','GND'):
 x,y=q[name];wire('GND',[(x,y),(x,825)]);dot(x,825)
wire('GND',[(1040,825),(1280,825)]);wire('GND',[(1160,825),(1160,860)]);gnd(1160,860)
wire('VBAT',[p['BAT+'],(490,610)],RED);flag(490,610,'VBAT',RED)
wire('GND',[p['BAT−'],(490,670),(490,710)]);gnd(490,710)
battery(230,890)
flag(1460,250,'VBAT',RED);wire('VBAT',[(1460,250),(1460,300)],RED)
resistor('R1','100k',(1460,300),(1460,420));wire('BAT_SENSE',[(1460,420),(1460,575),(1390,575),(1390,900),(900,900),(900,575),(1000,575)],BLUE);dot(1460,575)
resistor('R2','100k',(1460,575),(1460,710));ground_pin((1460,710))
wire('BAT_SENSE',[(1460,575),(1580,575)],BLUE);cap('C9','100nF',1580,575,710,side=1);ground_pin((1580,710))
text(1050,955,'Measure switched VBAT with a voltmeter. A3 should be about half VBAT.\nUSB may charge the connected cell; compare ADC and meter at the same time.\nR23/R24*: only when needed. ADS ALERT/RDY is unused.',12,ha='center')
save('T06_battery_adc')

# T07: no powered load is needed to verify the expander and the inverter gates.
start('T07 — PCF8574 and both enable inverters','Standalone meter test: amplifier, driver and motors disconnected. USB powers 3V3.',1800,1150)
p=board([('D4 / GPIO5',160),('D5 / GPIO6',215)],height=390,y=280)
q=pcf(720,345,['P1','P2','P3'])
wire('SDA',[p['D4 / GPIO5'],q['SDA']],BLUE);wire('SCL',[p['D5 / GPIO6'],q['SCL']],CYAN)
pullups(510,220,440,495)
for idx,yy,name in [(1,430,'P1'),(2,830,'P2')]:
 sx,sy=q[name];wire(name,[(sx,sy),(1100,sy),(1100,yy),(1190,yy)])
 out=inverter(1190,yy,idx,name);wire(f'EN{idx}',[out,(1630,out[1])]);text(1650,out[1],f'TP{idx}\n{"AMP SD" if idx==1 else "DRIVER SLP"}',11)
sy=q['P3'][1];wire('FAULT',[q['P3'],(1050,sy),(1050,990),(1400,990)])
resistor('R21','10k',(1400,990),(1500,990));wire('3V3',[(1500,990),(1550,990)],ORANGE);flag(1550,990)
text(710,1060,'Black meter probe → GND; red → TP1/TP2. P3 high here proves only its pull-up. Verify loaded enables later in T08/T11.',11,ha='center')
save('T07_pcf8574')

# Shared standalone motor / amplifier layouts.
for is_motor in (True,False):
 folder='T08_motors' if is_motor else 'T11_speaker';num='T08' if is_motor else 'T11'
 start(f'{num} — {"Motors + driver" if is_motor else "Amplifier + speaker"}', 'Complete individual test circuit. No sensors/OLED needed. USB is for upload/Serial; VBAT powers the load.',1950,1450)
 main=[('D4 / GPIO5',140),('D5 / GPIO6',195)]
 signal=[('D2 / GPIO3','AIN1'),('D3 / GPIO4','AIN2'),('D8 / GPIO7','BIN1'),('D9 / GPIO8','BIN2')] if is_motor else [('D6 / GPIO43','BCLK'),('D7 / GPIO44','LRC'),('D10 / GPIO9','DIN')]
 main += [(a,290+100*i) for i,(a,b) in enumerate(signal)]
 p=board(main,height=650,x=70,y=190)
 q=pcf(640,235,['P2','P3'] if is_motor else ['P1'])
 wire('SDA',[p['D4 / GPIO5'],q['SDA']],BLUE);wire('SCL',[p['D5 / GPIO6'],q['SCL']],CYAN)
 pullups(460,190,330,385)
 ys=480
 r=mod('DRV8833' if is_motor else 'MAX98357A',1270,400,320,560,left=[(b,80+100*i) for i,(a,b) in enumerate(signal)]+[('nSLEEP' if is_motor else 'SD',440)],top=[('VM' if is_motor else 'VIN',160)],bottom=[('GND',80)],right=[('AOUT1',100),('AOUT2',150),('BOUT1',260),('BOUT2',310),('nFAULT',450)] if is_motor else [('GAIN',95),('OUT+',240),('OUT−',300)],tint='#f1ecfa' if is_motor else '#edf7e9')
 for i,(a,b) in enumerate(signal):
  x,y=p[a];xx,yy=r[b]
  # Signal wires pass below the PCF body, then approach the load from the left.
  lane=1000+i*45;cross=970+i*55
  wire(b,[(x,y),(430+i*25,y),(430+i*25,lane),(cross,lane),(cross,yy),(xx,yy)],PURPLE if is_motor else GREEN)
  if is_motor:
   resistor(f'R{i+3}','100k',(1220,yy),(1220,yy+48),side=-1);dot(1220,yy);ground_pin((1220,yy+48))
 ground_pin(r['GND'])
 idx=2 if is_motor else 1;pinname='P2' if is_motor else 'P1'
 sx,sy=q[pinname];wire(pinname,[(sx,sy),(950,sy),(950,1220),(1010,1220)])
 out=inverter(1010,1220,idx,pinname)
 en='nSLEEP' if is_motor else 'SD'
 wire('ENABLE',[out,(1250,out[1]),(1250,r[en][1]),r[en]])
 if is_motor:
  wire('FAULT',[r['nFAULT'],(1640,850),(1640,1360),(980,1360),(980,q['P3'][1]),q['P3']])
  resistor('R21','10k',(1730,1115),(1830,1115));wire('FAULT',[(1640,1115),(1730,1115)]);dot(1640,1115)
  wire('3V3',[(1830,1115),(1860,1115)],ORANGE);flag(1860,1115)
  for k,yy in enumerate((525,685)):
   n1,n2=('AOUT1','AOUT2') if k==0 else ('BOUT1','BOUT2');ay=r[n1][1];by=r[n2][1]
   wire(n1,[r[n1],(1800,ay)],PURPLE);wire(n2,[r[n2],(1800,by)],PURPLE)
   cap(f'C{k+3}','100nF',1690,ay,by);dot(1690,ay);dot(1690,by)
   ax.add_patch(Circle((1840,(ay+by)/2),47,fc='#f1ecfa',ec=PURPLE,lw=1.8,zorder=4));text(1840,(ay+by)/2,'M',18,ha='center')
   text(1820,by+65,'LEFT' if k==0 else 'RIGHT',11,ha='center')
 else:
  wire('GAIN',[r['GAIN'],(1660,495)]);resistor('R22','100k',(1660,495),(1760,495));wire('VBAT',[(1760,495),(1810,495)],RED);flag(1810,495,'VBAT',RED)
  wire('SPK+', [r['OUT+'],(1750,640)],GREEN);wire('SPK-', [r['OUT−'],(1750,700)],GREEN)
  ax.add_patch(Rectangle((1750,640),25,60,fc='white',ec=GREEN,lw=1.7,zorder=4));ax.add_patch(Polygon([(1775,640),(1840,610),(1840,730),(1775,700)],fc='#edf7e9',ec=GREEN,lw=1.7,zorder=4))
  text(1755,790,'4Ω speaker\nNeither lead → GND',12,ha='center')
 # Independent fused 1S load supply: board USB and cell grounds are common.
 battery(1100,190)
 supply=r['VM' if is_motor else 'VIN'];x,y=supply
 if is_motor:
  wire('VBAT',[(1340,190),(1430,190),(1430,235)],RED)
  ax.plot([1430,1455],[235,285],c=RED,lw=2,zorder=5)
  for yy in (235,300):ax.add_patch(Circle((1430,yy),4,fc='white',ec=RED,lw=1.5,zorder=5))
  wire('VM',[(1430,300),(1430,400)],RED);text(1480,265,'SW2\nkill',11)
 else:wire('VBAT',[(1340,190),(1430,190),(1430,400)],RED)
 rail='VM' if is_motor else 'VBAT'
 wire(rail,[(1430,350),(1780,350)],RED);dot(1430,350)
 for ref,x,val,pol in [('C1' if is_motor else 'C5',1650,'1000µF' if is_motor else '100µF',True),('C2' if is_motor else 'C6',1780,'100nF',False)]:
  cap(ref,val,x,350,425,pol);dot(x,350);ground_pin((x,425))
 text(560,1220,'XIAO remains USB-powered in this isolated load test.\nCell negative and XIAO GND must be joined.\nBAT+ may stay disconnected; this test does not charge the cell.',11,ha='center')
 text(950,1390,'Wheels removed/restrained. Close SW2 only for controlled pulses. Isolate Sense SD pull-ups for D8/D9.' if is_motor else 'Use the Q1 inverter; remove conflicting SD/GAIN straps. Isolate Sense SD pull-ups for D10. Start at low volume.',11,ha='center')
 save(folder)

# T10 bumper switches.
start('T10 — Two bumper switches','Default NO parallel wiring: BUMPER_NC_SERIES=false. USB power only.',1500,900)
p=board([('D1 / GPIO2',210)],height=390,y=230)
wire('BUMPER',[p['D1 / GPIO2'],(1250,440)],'#905247')
power_pin((700,250));resistor('R14','10k',(700,250),(700,350));wire('BUMPER',[(700,350),(700,440)],'#905247');dot(700,440)
cap('C14','100nF',850,440,570);dot(850,440);ground_pin((850,570))
for i,x in enumerate((1050,1250),3):
 dot(x,440);wire('BUMPER',[(x,440),(x,500)],'#905247')
 ax.plot([x,x-24],[580,514],c='#905247',lw=2,zorder=5)
 for yy in (500,580):ax.add_patch(Circle((x,yy),4,fc='white',ec=GRAY,lw=1.5,zorder=5))
 wire('GND',[(x,580),(x,620)]);gnd(x,620)
 text(x+20,520,f'SW{i}\nNO',11);text(x+20,585,'COM',10)
text(850,750,'NC terminals unused. Press either switch: D1 becomes LOW. Test each switch separately.',12,ha='center');save('T10_bumper')

# T12 minimal sleep circuit: OLED + touch + battery, not full-robot sleep qualification.
start('T12 — Sleep / touch wake / battery current','Minimum test: XIAO + OLED + touch. No motors, amplifier, expander or edge sensors required.',1600,1050)
p=board([('D4 / GPIO5',150),('D5 / GPIO6',210),('D0 / GPIO1',310),('BAT+',420),('BAT−',475)],height=530,y=210)
q=simple_oled(1000,265)
wire('SDA',[p['D4 / GPIO5'],q['SDA']],BLUE);wire('SCL',[p['D5 / GPIO6'],q['SCL']],CYAN)
pullups(670,180,360,420);touch(p['D0 / GPIO1'],850,550)
wire('VBAT',[p['BAT+'],(500,630)],RED);flag(500,630,'VBAT',RED)
wire('GND',[p['BAT−'],(500,685),(500,720)]);gnd(500,720)
battery(280,850,ammeter=True)
text(1140,825,'Upload with USB first. Then unplug USB.\nInsert the fused meter IN SERIES with cell positive.\nNever put an ammeter across the battery.\nRecord current; there is no universal pass value.',12,ha='center')
text(850,970,'This sketch tests deliberate touch wake. Full-robot sleep/current must also be tested with code/bob firmware.',11,ha='center');save('T12_sleep_wake')

# T13 USB power + radio path; Wi-Fi is not an electrical jumper.
start('T13 — Wi-Fi / laptop link','Only XIAO + antenna + USB power required. Network path is dashed, not a wire.',1500,850)
p=board([],height=330,y=200)
ax.add_patch(Rectangle((1020,230),350,220,fc='#f2f5f8',ec=INK,lw=1.6,zorder=3));text(1195,290,'Laptop',18,ha='center',bold=True)
text(1195,355,'code/laptop/server.py\nLAN IP : 8765 / bob',13,ha='center')
wire('RADIO',[(420,400),(1020,400)],BLUE,dashed=True)
text(710,350,'Same 2.4 GHz LAN\nshared BOB_TOKEN',13,ha='center')
text(780,620,'Fit the antenna. Copy secrets.example.h → secrets.h; set Wi-Fi, laptop LAN IP and BOB_TOKEN.\nStart server with --host YOUR_LAN_IP --no-stt. This test does not arm or move motors.',12,ha='center')
save('T13_wifi_link')

# T03: only bus devices, with three separate mux branches.
start('T03 — I²C bus + three VL53L0X branches','USB power only. This checks addresses; T09 checks sensor identity, ranges and edge calibration.',2100,1600)
p=board([('D4 / GPIO5',160),('D5 / GPIO6',220)],height=420,x=80,y=220)
wire('SDA',[(550,160),(550,1160)],BLUE);wire('SCL',[(600,190),(600,1160)],CYAN)
wire('SDA',[p['D4 / GPIO5'],(550,380)],BLUE);dot(550,380)
wire('SCL',[p['D5 / GPIO6'],(600,440)],CYAN);dot(600,440)
for title,y,h,bottom in [('SSD1306 • 0x3C',250,220,[('GND',160)]),('ADS1115 • 0x48',600,280,[('A0–A3',70),('ADDR',170),('GND',270)]),('PCF8574 • 0x20',1000,250,[('A0–A2',80),('GND',250)])]:
 q=mod(title,760,y,330,h,left=[('SDA',95),('SCL',150)],top=[('VCC / VDD',160)],bottom=bottom)
 power_pin(q['VCC / VDD'])
 for n,col,x in [('SDA',BLUE,550),('SCL',CYAN,600)]:
  xx,yy=q[n];wire(n,[(x,yy),q[n]],col);dot(x,yy)
 for name,xx in bottom:ground_pin(q[name])
 if title.startswith('PCF'):text(925,y+195,'P0–P7 and INT: NC',10,ha='center')
 if title.startswith('ADS'):text(925,y+205,'ALERT/RDY: NC',10,ha='center')
m=mod('TCA9548A • 0x70',1270,220,300,1150,left=[('SDA',95),('SCL',150),('RESET',1030)],right=[('SD0',220),('SC0',260),('SD1',540),('SC1',580),('SD2',860),('SC2',900)],top=[('VCC',150)],bottom=[('A0',40),('A1',110),('A2',180),('GND',250)])
power_pin(m['VCC'])
wire('SDA',[(550,160),(1170,160),(1170,315),m['SDA']],BLUE)
wire('SCL',[(600,190),(1200,190),(1200,370),m['SCL']],CYAN)
for n in ('A0','A1','A2','GND'):ground_pin(m[n])
text(1420,1430,'CH3–7: NC',11,ha='center')
wire('RESET',[m['RESET'],(1220,1250)])
resistor('R25','10k',(1130,1250),(1220,1250),True);wire('3V3',[(1100,1250),(1130,1250)],ORANGE);flag(1100,1250)
for i,(name,y) in enumerate([('LEFT',360),('RIGHT',680),('CENTER',1000)]):
 q=mod(name+' VL53L0X',1760,y,270,190,left=[('SDA',80),('SCL',120),('XSHUT',165)],right=[('GPIO1',165)],top=[('VIN*',100)],bottom=[('GND',100)],tint='#f4eff9')
 power_pin(q['VIN*']);ground_pin(q['GND']);nc(q['GPIO1'])
 for j,(n,col) in enumerate([('SDA',BLUE),('SCL',CYAN)]):
  chan=f'{"SD" if j==0 else "SC"}{i}';wire(chan,[m[chan],q[n]],col)
  xx=1640+j*70;power_pin((xx,y-5),net='VIO_'+name[0]);resistor(f'R{26+i*2+j}','4.7k',(xx,y-5),(xx,y+45),True,side=-1)
  wire(chan,[(xx,y+45),(xx,q[n][1])],col);dot(xx,q[n][1])
 yy=y+165
 wire('XSHUT'+str(i),[q['XSHUT'],(1740,yy),(1740,yy+35)])
 resistor(f'R{32+i}','10k',(1660,yy+35),(1740,yy+35),True)
 wire('VLOGIC'+str(i),[(1600,yy+35),(1660,yy+35)],ORANGE);flag(1610,yy+35,'VLOGIC_'+name[0])
for x,n,ref,col in [(550,'SDA','R23',BLUE),(600,'SCL','R24',CYAN)]:
 resistor(ref,'4.7k',(x,1160),(x,1240),True,side=-1 if x==550 else 1)
 wire('3V3',[(x,1240),(x,1300)],ORANGE);flag(x,1320)
text(370,840,'Expected upstream: 0x3C, 0x48, 0x20, 0x70.\nEach mux branch: one 0x29.\nAll analog ADC inputs grounded in this scan-only build;\nuse T06 wiring for battery measurement.',11,ha='center')
text(1050,1510,'* Add pull-ups only if missing/needed. Verify 3.3 V VIN compatibility. VIO = carrier bus rail; VLOGIC = sensor logic rail.\nLeave XSHUT header unwired only if its correct pull-up is already fitted. GPIO1 is unused.',11,ha='center')
save('T03_i2c_scan')

# T09 intentionally uses the production firmware and the complete robot circuit.
for ext in ('png','svg'):
 shutil.copyfile(ROOT/'images'/f'bob-wiring.{ext}',TESTS/'T09_edge_sensors'/f'circuit.{ext}')
print('Generated circuit.png + circuit.svg in all 13 hardware test folders.')
