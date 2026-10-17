#!/usr/bin/env python3
"""Draw the complete pin-to-pin robot schematic and detail views.

Uses module pin symbols, individual external passives, junction dots and wire
bridges. The JSON netlist records terminals, not physical header numbering.
Run with Python + Matplotlib; no hardware access and no image-generation model.
"""
from pathlib import Path
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Arc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'images'
plt.rcParams.update({'svg.fonttype': 'none', 'svg.hashsalt': 'bob-pin-schematic',
                     'font.family': 'DejaVu Sans'})
W, H = 3600, 2800
fig, ax = plt.subplots(figsize=(36, 28))
fig.subplots_adjust(0, 0, 1, 1)
ax.set(xlim=(0, W), ylim=(H, 0), aspect='equal')
ax.axis('off')
C = dict(VBAT='#d32935', VM='#d32935', V3='#ea7900', SDA='#087bb8',
         SCL='#00a7bc', motor='#8051bc', audio='#268d35', touch='#c57416',
         bumper='#905247', ctl='#60666c', GND='#40464d', branch='#147d9c')
INK = '#18202a'
segments, pins, junctions, texts, boxes = [], {}, [], [], []

def text(x, y, value, size=12, color=INK, ha='left', weight='normal', **kw):
    obj=ax.text(x,y,value,fontsize=size,color=color,ha=ha,va='center',
                weight=weight,zorder=12,**kw)
    texts.append(obj)
    return obj

def wire(net, points, color=None, lw=2):
    color = color or C.get(net, C['ctl'])
    ax.plot(*zip(*points),color=color,lw=lw,zorder=2,solid_capstyle='round')
    for a,b in zip(points,points[1:]):
        assert a[0]==b[0] or a[1]==b[1], (net,a,b)
        segments.append((net,a,b,color,lw))

def terminal(ref, pin, xy, net):
    key=f'{ref}.{pin}'
    assert key not in pins, key
    pins[key]={'net':net, 'xy':xy}

def dot(x,y,net):
    junctions.append((x,y,net))

def flag(net,x,y,color=None,ha='center'):
    color=color or C.get(net,C['ctl'])
    text(x,y,net,11,'white',ha=ha,weight='bold',
         bbox=dict(boxstyle='round,pad=.18',fc=color,ec=color,lw=.5))

def ground(x,y,start=None):
    if start is not None: wire('GND',[start,(x,y)],C['GND'])
    for d,width in ((0,32),(8,22),(16,10)):
        ax.plot([x-width/2,x+width/2],[y+d,y+d],c=C['GND'],lw=1.8,zorder=5)

def nc(ref,pin,x,y,side='right'):
    terminal(ref,pin,(x,y),'NC')
    dx=16 if side=='right' else -16 if side=='left' else 0
    dy=16 if side=='bottom' else 0
    ax.plot([x,x+dx],[y,y+dy],c=C['ctl'],lw=1.5,zorder=5)
    xx,yy=x+dx,y+dy
    ax.plot([xx-5,xx+5],[yy-5,yy+5],c=C['ctl'],lw=1.4,zorder=5)
    ax.plot([xx-5,xx+5],[yy+5,yy-5],c=C['ctl'],lw=1.4,zorder=5)

def body(ref,title,x,y,w,h,tint='#f1f5fa',subtitle=None):
    ax.add_patch(Rectangle((x,y),w,h,fc=tint,ec='#405468',lw=1.8,zorder=4))
    boxes.append((ref,x,y,w,h))
    if ref in ('U6','U7','U8'):
        text(x+w*.38,y+h*.48,title.replace(' VL53L0X','\nVL53L0X')+f'\n{ref} • 0x29',14,ha='center',weight='bold')
    else:
        text(x+w/2,y+25,title,15,ha='center',weight='bold')
        if subtitle: text(x+w/2,y+52,subtitle,10,ha='center')

def pin(ref,name,x,y,net,side='left',label=None):
    terminal(ref,name,(x,y),net)
    if side=='left': text(x+12,y,label or name,11)
    elif side=='right': text(x-12,y,label or name,11,ha='right')
    elif side=='top': text(x-12,y-14,label or name,10,ha='right')
    else: text(x,y-14,label or name,10,ha='center')

def resistor(ref,value,a,b,na,nb,color=None,optional=False,label_side=1):
    terminal(ref,'1',a,na);terminal(ref,'2',b,nb)
    x1,y1=a;x2,y2=b
    color=color or C['ctl']
    dx,dy=x2-x1,y2-y1;length=math.hypot(dx,dy)
    ux,uy=dx/length,dy/length;px,py=-uy,ux
    shape=[]
    for t,off in [(0,0),(.2,0),(.27,7),(.36,-7),(.45,7),(.54,-7),(.63,7),(.72,-7),(.8,0),(1,0)]:
        shape.append((x1+dx*t+px*off,y1+dy*t+py*off))
    ax.plot(*zip(*shape),c=color,lw=1.8,zorder=6)
    label=f'{ref}{"*" if optional else ""}\n{value}'
    if x1==x2:
        text(x1+label_side*19,(y1+y2)/2,label,10,ha='left' if label_side>0 else 'right')
    else:text((x1+x2)/2,y1-29,label,10,ha='center')

def capacitor(ref,value,a,b,na,nb,polar=False,label_side=1):
    terminal(ref,'1',a,na);terminal(ref,'2',b,nb)
    x1,y1=a;x2,y2=b
    assert x1==x2
    mid=(y1+y2)/2
    ax.plot([x1,x1],[y1,mid-5],c=C['ctl'],lw=1.8,zorder=6)
    ax.plot([x1,x1],[mid+5,y2],c=C['ctl'],lw=1.8,zorder=6)
    for yy in (mid-5,mid+5):ax.plot([x1-16,x1+16],[yy,yy],c=C['ctl'],lw=2,zorder=6)
    text(x1+label_side*23,mid,f'{ref}\n{value}',10,ha='left' if label_side>0 else 'right')
    if polar:text(x1-24,mid-17,'+',12,C['VBAT'])

def switch(ref,a,b,na,nb,label):
    terminal(ref,'1',a,na);terminal(ref,'2',b,nb)
    x1,y1=a;x2,y2=b
    if y1==y2:
        xx1=x1+12;xx2=x2-12
        ax.plot([x1,xx1],[y1,y1],c=C['VBAT'],lw=2,zorder=6)
        ax.plot([xx2,x2],[y1,y1],c=C['VBAT'],lw=2,zorder=6)
        ax.plot([xx1,xx2-5],[y1,y1-28],c=C['VBAT'],lw=2,zorder=6)
        for x in (xx1,xx2):ax.add_patch(Circle((x,y1),5,fc='white',ec=C['VBAT'],lw=1.6,zorder=7))
        text((x1+x2)/2,y1-60,f'{ref}\n{label}',11,ha='center',weight='bold')
    else:
        ax.plot([x1,x1],[y1,y1+12],c=C['VBAT'],lw=2,zorder=6)
        ax.plot([x1,x1],[y2-12,y2],c=C['VBAT'],lw=2,zorder=6)
        ax.plot([x1,x1+28],[y2-12,y1+17],c=C['VBAT'],lw=2,zorder=6)
        for y in (y1+12,y2-12):ax.add_patch(Circle((x1,y),5,fc='white',ec=C['VBAT'],lw=1.6,zorder=7))
        text(x1+45,(y1+y2)/2,f'{ref}\n{label}',11,weight='bold')

def bumper(ref,x,y):
    terminal(ref,'NO',(x,y),'BUMPER');terminal(ref,'COM',(x,y+90),'GND')
    wire('BUMPER',[(x,y),(x,y+20)],C['bumper'])
    wire('GND',[(x,y+70),(x,y+90)],C['GND'])
    ax.plot([x,x-22],[y+70,y+28],c=C['bumper'],lw=2,zorder=6)
    for yy in (y+20,y+70):ax.add_patch(Circle((x,yy),4,fc='white',ec=C['bumper'],lw=1.5,zorder=7))
    text(x-28,y+38,f'{ref}\nNO',10,ha='right')
    text(x+13,y+75,'COM',9)
    ground(x,y+110,start=(x,y+90))

def npn(ref,x,y,base_net,out_net):
    # B=(x,y); C=(x+40,y-40); E=(x+40,y+40)
    terminal(ref,'B',(x,y),base_net);terminal(ref,'C',(x+40,y-40),out_net);terminal(ref,'E',(x+40,y+40),'GND')
    ax.plot([x,x],[y-22,y+22],c=C['ctl'],lw=2,zorder=6)
    ax.plot([x,x+40],[y-12,y-40],c=C['ctl'],lw=2,zorder=6)
    ax.plot([x,x+40],[y+12,y+40],c=C['ctl'],lw=2,zorder=6)
    ax.annotate('',xy=(x+36,y+37),xytext=(x+15,y+22),arrowprops=dict(arrowstyle='-|>',lw=1.5,color=C['ctl']),zorder=7)
    text(x+64,y,f'{ref}\nBC547\nNPN',12,weight='bold')
    text(x-11,y+18,'B',10,ha='right');text(x+40,y-53,'C',10);text(x+40,y+54,'E',10)

# Heading and reading key.
text(W/2,55,'Bob — complete pin-to-pin circuit',27,ha='center',weight='bold')
text(W/2,102,'XIAO ESP32-S3 Sense  •  three downward VL53L0X modules  •  revision 3.2 drawing / unchanged revision 3.1 electrical design',14,ha='center')
text(W/2,140,'DOT = joined wires     BRIDGE = crossing, not joined     GND symbols = common ground     Identical power / BAT_SENSE labels = the same wire',12,ha='center')

# Three individual downward sensor modules and their separate mux wires.
body('U5','TCA9548A',760,340,280,760,'#edf6f9','0x70 • only one channel at a time')
for i,(side,yy) in enumerate((('LEFT',320),('RIGHT',620),('CENTER',920))):
    ref=f'U{6+i}';sd=f'SD{i}';sc=f'SC{i}';logic=f'VLOGIC_{side[0]}';vio=f'VIO_{side[0]}'
    body(ref,f'{side} VL53L0X',60,yy,350,200,'#f7effa',f'{ref} • Robu carrier • 0x29')
    # Sensor signal pin labels lie inside right edge, physical header order is not implied.
    pin(ref,'SDA',410,yy+50,sd,'right');pin(ref,'SCL',410,yy+100,sc,'right')
    pin(ref,'XSHUT',410,yy+150,f'XSHUT_{side[0]}','right')
    pin(ref,'VIN',140,yy,'3V3','top',label='VIN / VCC*')
    pin(ref,'GND',140,yy+200,'GND','bottom')
    text(300,yy+184,'GPIO1',10,ha='center');nc(ref,'GPIO1',300,yy+200,'bottom')
    wire('3V3',[(140,yy),(140,yy-35)],C['V3']);flag('3V3',140,yy-45,C['V3'])
    ground(140,yy+245,start=(140,yy+200))
    pin('U5',sd,760,yy+50,sd,'left');pin('U5',sc,760,yy+100,sc,'left')
    wire(sd,[(410,yy+50),(760,yy+50)],C['SDA'])
    wire(sc,[(410,yy+100),(760,yy+100)],C['SCL'])
    # Optional per-branch pull-ups, each to the verified carrier interface rail.
    for j,(xx,net,target) in enumerate(((500,sd,yy+50),(620,sc,yy+100))):
        wire(vio,[(xx,yy-60),(xx,yy-30)],C['V3'])
        resistor(f'R{26+2*i+j}','4.7k',(xx,yy-30),(xx,yy+20),vio,net,optional=True,label_side=-1 if j==0 else 1)
        wire(net,[(xx,yy+20),(xx,target)],C['SDA'] if j==0 else C['SCL']);dot(xx,target,net)
    wire(vio,[(500,yy-60),(620,yy-60)],C['V3']);flag(vio,560,yy-60,C['V3'])
    shut=f'XSHUT_{side[0]}'
    wire(shut,[(410,yy+150),(450,yy+150),(450,yy+185),(495,yy+185)],C['ctl'])
    resistor(f'R{32+i}','10k',(495,yy+185),(595,yy+185),shut,logic,optional=True)
    wire(logic,[(595,yy+185),(685,yy+185)],C['V3']);flag(logic,685,yy+185,C['V3'])

pin('U5','VCC',850,340,'3V3','top');wire('3V3',[(850,340),(850,295)],C['V3']);flag('3V3',850,280,C['V3'])
pin('U5','SDA',1040,630,'SDA','right');pin('U5','SCL',1040,680,'SCL','right')
wire('SDA',[(1040,630),(1290,630)],C['SDA']);dot(1290,630,'SDA')
wire('SCL',[(1040,680),(1240,680)],C['SCL']);dot(1240,680,'SCL')
pin('U5','RESET',1040,540,'MUX_RESET','right')
wire('MUX_RESET',[(1040,540),(1070,540)])
resistor('R25','10k',(1070,540),(1140,540),'MUX_RESET','3V3',optional=True)
wire('3V3',[(1140,540),(1160,540)],C['V3']);flag('3V3',1160,540,C['V3'])
for x,name in ((800,'GND'),(860,'A0'),(920,'A1'),(980,'A2')):
    pin('U5',name,x,1100,'GND','bottom');wire('GND',[(x,1100),(x,1150)],C['GND']);dot(x,1150,'GND')
wire('GND',[(800,1150),(980,1150)],C['GND']);ground(890,1180,start=(890,1150))
for idx,y in enumerate((780,830,880,930,980),3):
    text(1028,y,f'SD{idx} / SC{idx}',10,ha='right')
    # Both unused pins are explicitly recorded, the slash is a pair designation.
    nc('U5',f'SD{idx}',1040,y);nc('U5',f'SC{idx}',1040,y+13)

# Shared bus and its optional pull-ups.
wire('SDA',[(1290,450),(1290,2070)],C['SDA'])
wire('SCL',[(1200,450),(1200,560),(1240,560),(1240,2130)],C['SCL'])
for ref,x,net in (('R23',1290,'SDA'),('R24',1200,'SCL')):
    resistor(ref,'4.7k',(x,370),(x,450),'3V3',net,optional=True,label_side=1 if x==1290 else -1)
    wire('3V3',[(x,370),(x,320)],C['V3'])
wire('3V3',[(1200,320),(1290,320)],C['V3']);flag('3V3',1245,300,C['V3'])
text(1194,1520,'SCL',11,C['SCL'],ha='right');text(1305,1520,'SDA',11,C['SDA'])

# OLED, ADC and expander have every external terminal shown.
body('U2','SSD1306 OLED',790,1260,280,160,'#f3f4f6','U2 • 128×64 • 0x3C')
for label,y,net in (('SDA',1330,'SDA'),('SCL',1380,'SCL')):
    pin('U2',label,1070,y,net,'right');wire(net,[(1070,y),(1290 if net=='SDA' else 1240,y)],C[net]);dot(1290 if net=='SDA' else 1240,y,net)
pin('U2','VCC',790,1330,'3V3');wire('3V3',[(790,1330),(735,1330)],C['V3']);flag('3V3',718,1330,C['V3'])
pin('U2','GND',790,1380,'GND');wire('GND',[(790,1380),(755,1380),(755,1440)],C['GND']);ground(755,1440)
body('U3','ADS1115',790,1500,280,330,'#f3f4f6','U3 • 0x48 • battery only')
for label,y,net in (('SDA',1590,'SDA'),('SCL',1640,'SCL')):
    pin('U3',label,1070,y,net,'right');wire(net,[(1070,y),(1290 if net=='SDA' else 1240,y)],C[net]);dot(1290 if net=='SDA' else 1240,y,net)
pin('U3','A3',790,1590,'BAT_SENSE');wire('BAT_SENSE',[(790,1590),(700,1590)],C['VBAT']);flag('BAT_SENSE',650,1590,C['VBAT'])
for name,y in (('A0',1660),('A1',1710),('A2',1760)):
    pin('U3',name,790,y,'GND');wire('GND',[(790,y),(720,y)],C['GND']);dot(720,y,'GND')
wire('GND',[(720,1660),(720,1810)],C['GND']);ground(720,1810)
for name,x in (('ADDR',900),('GND',980)):
    pin('U3',name,x,1830,'GND','bottom');wire('GND',[(x,1830),(x,1880)],C['GND']);dot(x,1880,'GND')
wire('GND',[(900,1880),(980,1880)],C['GND']);ground(940,1910,start=(940,1880))
pin('U3','VDD',900,1500,'3V3','top');wire('3V3',[(900,1500),(900,1460)],C['V3']);flag('3V3',900,1440,C['V3'])
text(1058,1740,'ALERT/RDY',10,ha='right');nc('U3','ALERT',1070,1740)
body('U4','PCF8574',790,2010,280,450,'#f3f4f6','U4 • 0x20')
for name,y,net in (('SDA',2100,'SDA'),('SCL',2150,'SCL'),('P1',2200,'AMP_CTL'),('P2',2270,'DRV_CTL'),('P3',2340,'FAULT')):
    pin('U4',name,1070,y,net,'right')
    if name in ('SDA','SCL'):
        # Extend the main trunks to these exact terminal rows.
        end=1290 if name=='SDA' else 1240
        wire(net,[(end,2070 if name=='SDA' else 2130),(end,y),(1070,y)],C[net])
for idx,y in enumerate((2100,2160,2220,2280,2340,2400)):
    name=('P0','P4','P5','P6','P7','INT')[idx]
    text(802,y,name,10);nc('U4',name,790,y,'left')
for name,x in (('A0',830),('A1',890),('A2',950),('GND',1010)):
    pin('U4',name,x,2460,'GND','bottom');wire('GND',[(x,2460),(x,2510)],C['GND']);dot(x,2510,'GND')
wire('GND',[(830,2510),(1010,2510)],C['GND']);ground(920,2545,start=(920,2510))
pin('U4','VCC',900,2010,'3V3','top');wire('3V3',[(900,2010),(900,1965)],C['V3']);flag('3V3',900,1945,C['V3'])

# Central controller — same familiar header arrangement as the sample.
body('U1','Seeed XIAO',1450,900,390,740,'#e9f2ff','ESP32-S3 Sense • U1')
ax.add_patch(Rectangle((1560,865),170,35,fc='#d9dce0',ec='#66717d',lw=1.2,zorder=5));text(1645,881,'USB-C',10,ha='center')
left=[('D0',970,'TOUCH','D0  GPIO1'),('D1',1040,'BUMPER','D1  GPIO2'),('D2',1110,'AIN1','D2  GPIO3'),('D3',1180,'AIN2','D3  GPIO4'),('D4',1360,'SDA','D4  GPIO5'),('D5',1430,'SCL','D5  GPIO6'),('D6',1580,'BCLK','D6  GPIO43')]
for name,y,net,label in left:pin('U1',name,1450,y,net,label=label)
for name,y,net,label in [('GND',1110,'GND','GND'),('3V3',1180,'3V3','3V3'),('D10',1320,'DIN','GPIO9  D10'),('D9',1390,'BIN2','GPIO8  D9'),('D8',1460,'BIN1','GPIO7  D8'),('D7',1530,'LRC','GPIO44  D7')]:pin('U1',name,1840,y,net,'right',label)
text(1828,1040,'5V',11,ha='right');nc('U1','5V',1840,1040)
pin('U1','BAT-',1560,1640,'GND','bottom');ground(1560,1690,start=(1560,1640))
pin('U1','BAT+',1760,1640,'VBAT','bottom')
wire('GND',[(1840,1110),(1880,1110),(1880,1145)],C['GND']);ground(1880,1145)
wire('SDA',[(1450,1360),(1290,1360)],C['SDA']);dot(1290,1360,'SDA')
wire('SCL',[(1450,1430),(1240,1430)],C['SCL']);dot(1240,1430,'SCL')
text(1645,1250,'Sense camera + microphone\nuse the fitted expansion board.\nNo external camera wires.',12,'#406184',ha='center')
wire('3V3',[(1840,1180),(2100,1180)],C['V3']);flag('3V3',2100,1160,C['V3'])
for ref,x,val,pol in [('C7',1980,'10µF',True),('C8',2090,'100nF',False)]:
    capacitor(ref,val,(x,1180),(x,1270),'3V3','GND',pol,label_side=-1 if ref=='C7' else 1);dot(x,1180,'3V3');ground(x,1285,start=(x,1270))

# Touch and two separate bumper switches.
ax.add_patch(Rectangle((1330,240),190,120,fc='#fbe6c9',ec=C['touch'],lw=1.8,zorder=4))
text(1425,280,'Copper touch pad',13,ha='center',weight='bold');text(1425,319,'Insulate from chassis',10,ha='center')
terminal('TP1','PAD',(1400,360),'TOUCH_PAD')
wire('TOUCH_PAD',[(1400,360),(1400,420)],C['touch'])
resistor('R13','470Ω',(1400,420),(1400,500),'TOUCH_PAD','TOUCH',C['touch'])
wire('TOUCH',[(1400,500),(1400,970),(1450,970)],C['touch'])
wire('BUMPER',[(1450,1040),(1370,1040),(1370,590),(1930,590)],C['bumper'])
for ref,x in [('SW3',1580),('SW4',1710)]:
    bumper(ref,x,590);dot(x,590,'BUMPER')
text(1660,400,'Two bumper microswitches',15,ha='center',weight='bold')
text(1660,438,'COM + NO contacts • parallel • pressed = LOW\nNC terminals unused • firmware NC option = false',11,ha='center')
resistor('R14','10k',(1830,490),(1830,590),'3V3','BUMPER',C['bumper'])
wire('3V3',[(1830,490),(1830,475)],C['V3']);flag('3V3',1830,480,C['V3']);dot(1830,590,'BUMPER')
capacitor('C14','100nF',(1930,590),(1930,680),'BUMPER','GND');dot(1930,590,'BUMPER');ground(1930,710,start=(1930,680))

# Actual cell symbol, fuse, switches, divider and reservoir capacitors.
text(2760,215,'POWER — one protected 1S cell',18,ha='center',weight='bold')
terminal('BT1','+',(2420,310),'CELL+');terminal('BT1','-',(2420,600),'GND')
wire('CELL+',[(2420,310),(2490,310)],C['VBAT'])
# Battery long/short plates, no unexplained power block.
ax.plot([2420,2420],[310,410],c=C['VBAT'],lw=2,zorder=6)
for yy,ww in ((410,68),(450,36)):
    ax.plot([2420-ww/2,2420+ww/2],[yy,yy],c=C['ctl'],lw=2.5,zorder=6)
ax.plot([2420,2420],[450,600],c=C['GND'],lw=2,zorder=6)
text(2370,370,'+',15,C['VBAT']);text(2370,495,'−',15)
text(2340,440,'BT1\nProtected 18650\n1S / 4.2 V full',12,ha='right');ground(2420,620,start=(2420,600))
terminal('F1','1',(2490,310),'CELL+');terminal('F1','2',(2570,310),'FUSED+')
ax.add_patch(Rectangle((2490,300),80,20,fc='white',ec=C['VBAT'],lw=1.8,zorder=5));ax.plot([2490,2570],[310,310],c=C['VBAT'],lw=1,zorder=6)
text(2530,270,'F1\nfuse',11,ha='center')
wire('FUSED+',[(2570,310),(2630,310)],C['VBAT']);switch('SW1',(2630,310),(2730,310),'FUSED+','VBAT','MAIN')
wire('VBAT',[(2730,310),(3330,310)],C['VBAT']);flag('VBAT',3060,310,C['VBAT'])
wire('VBAT',[(2830,310),(2830,420)],C['VBAT']);dot(2830,310,'VBAT')
switch('SW2',(2830,420),(2830,540),'VBAT','VM','MOTOR KILL')
wire('VM',[(2830,540),(2830,900),(2520,900),(2520,1120)],C['VM']);flag('VM',2830,690,C['VM'])
wire('VBAT',[(2900,310),(2900,760),(1920,760),(1920,1720),(1760,1720),(1760,1640)],C['VBAT']);dot(2900,310,'VBAT')
resistor('R1','100k',(3330,310),(3330,450),'VBAT','BAT_SENSE',C['VBAT'])
wire('BAT_SENSE',[(3330,450),(3330,490),(3470,490)],C['VBAT']);dot(3330,490,'BAT_SENSE');flag('BAT_SENSE',3210,490,C['VBAT']);wire('BAT_SENSE',[(3210,490),(3330,490)],C['VBAT'])
resistor('R2','100k',(3330,490),(3330,610),'BAT_SENSE','GND',C['VBAT']);ground(3330,650,start=(3330,610))
capacitor('C9','100nF',(3470,490),(3470,610),'BAT_SENSE','GND',label_side=-1);ground(3470,650,start=(3470,610))
text(3130,685,'BAT_SENSE → ADS1115 A3\n≈2.1 V at full battery charge',11,ha='center')
text(3150,815,'USB-C uses the XIAO charger. No second charger.\nSW1 is not USB isolation; SW2 physically opens VM.',11,ha='center')
for ref,x,val,pol in [('C1',2610,'1000µF',True),('C2',2750,'100nF',False)]:
    capacitor(ref,val,(x,900),(x,1040),'VM','GND',pol);dot(x,900,'VM');ground(x,1070,start=(x,1040))

# Motor driver, all four input pulldowns, and individual motors/capacitors.
body('U9','DRV8833 driver',2440,1120,390,530,'#f1eafa','U9 • carrier with SLP + FLT exposed')
pin('U9','VM',2520,1120,'VM','top')
for name,y in [('AIN1',1200),('AIN2',1310),('BIN1',1420),('BIN2',1530)]:pin('U9',name,2440,y,name)
wire('AIN1',[(1450,1110),(1390,1110),(1390,790),(2200,790),(2200,1200),(2440,1200)],C['motor'])
wire('AIN2',[(1450,1180),(1350,1180),(1350,740),(2250,740),(2250,1310),(2440,1310)],C['motor'])
wire('BIN1',[(1840,1460),(2140,1460),(2140,1420),(2440,1420)],C['motor'])
wire('BIN2',[(1840,1390),(2180,1390),(2180,1530),(2440,1530)],'#a67bda')
for i,(name,y) in enumerate([('AIN1',1200),('AIN2',1310),('BIN1',1420),('BIN2',1530)],3):
    resistor(f'R{i}','100k',(2360,y),(2360,y+65),name,'GND',C['motor'],label_side=-1);dot(2360,y,name);ground(2360,y+83,start=(2360,y+65))
for name,x,net in [('GND',2480,'GND'),('nSLEEP',2570,'DRIVER_EN'),('nFAULT',2750,'FAULT')]:pin('U9',name,x,1650,net,'bottom')
ground(2480,1700,start=(2480,1650))
for idx,cy in enumerate((1265,1465)):
    prefix='A' if idx==0 else 'B';mot=f'M{idx+1}'
    for n,yy in ((1,cy-25),(2,cy+25)):
        net=f'{prefix}OUT{n}';pin('U9',net,2830,yy,net,'right');wire(net,[(2830,yy),(3150,yy)],C['motor']);terminal(mot,str(n),(3150,yy),net)
    capacitor(f'C{idx+3}','100nF',(3030,cy-25),(3030,cy+25),f'{prefix}OUT1',f'{prefix}OUT2');dot(3030,cy-25,f'{prefix}OUT1');dot(3030,cy+25,f'{prefix}OUT2')
    ax.add_patch(Circle((3210,cy),65,fc='#f1eafa',ec=C['motor'],lw=2,zorder=5))
    text(3210,cy,'M',22,C['motor'],ha='center',weight='bold')
    text(3300,cy,f'{mot}  {"LEFT" if idx==0 else "RIGHT"}\nN12 gearmotor\nencoder wires NC',12)

# Audio I2S signals, amplifier, gain resistor, decoupling and speaker.
body('U10','MAX98357A',1750,1860,350,380,'#eaf6e8','U10 • I²S amplifier (A version)')
for name,y,net in [('BCLK',1920,'BCLK'),('LRC',2000,'LRC'),('DIN',2080,'DIN'),('SD',2160,'AMP_EN')]:pin('U10',name,1750,y,net)
wire('BCLK',[(1450,1580),(1330,1580),(1330,1920),(1750,1920)],C['audio'])
wire('LRC',[(1840,1530),(2080,1530),(2080,1740),(1600,1740),(1600,2000),(1750,2000)],C['audio'])
wire('DIN',[(1840,1320),(2210,1320),(2210,1780),(1660,1780),(1660,2080),(1750,2080)],C['audio'])
pin('U10','VIN',1840,1860,'VBAT','top');wire('VBAT',[(1840,1860),(1840,1815)],C['VBAT']);flag('VBAT',1840,1805,C['VBAT'])
pin('U10','GND',1800,2240,'GND','bottom');ground(1800,2290,start=(1800,2240))
pin('U10','GAIN',2100,1920,'GAIN','right');wire('GAIN',[(2100,1920),(2170,1920)])
resistor('R22','100k',(2170,1920),(2270,1920),'GAIN','VBAT');wire('VBAT',[(2270,1920),(2310,1920)],C['VBAT']);flag('VBAT',2310,1920,C['VBAT'])
wire('VBAT',[(2200,2010),(2340,2010)],C['VBAT']);flag('VBAT',2270,1980,C['VBAT']);wire('VBAT',[(2270,1980),(2270,2010)],C['VBAT'])
for ref,x,val,pol in [('C5',2200,'100µF',True),('C6',2340,'100nF',False)]:
    capacitor(ref,val,(x,2010),(x,2140),'VBAT','GND',pol);ground(x,2170,start=(x,2140))
for name,x,net in [('OUT+',1920,'SPK+'),('OUT-',2020,'SPK-')]:pin('U10',name,x,2240,net,'bottom')
wire('SPK+',[(1920,2240),(1920,2320),(2110,2320)],C['audio'])
wire('SPK-',[(2020,2240),(2020,2400),(2110,2400)],C['audio'])
terminal('SPK1','+',(2110,2320),'SPK+');terminal('SPK1','-',(2110,2400),'SPK-')
ax.add_patch(Rectangle((2110,2320),30,80,fc='white',ec=C['audio'],lw=2,zorder=5))
ax.add_patch(Polygon([(2140,2320),(2220,2280),(2220,2440),(2140,2400)],fc='#eaf6e8',ec=C['audio'],lw=2,zorder=5))
text(2120,2480,'SPK1  4Ω speaker\nNeither terminal goes to GND',12,ha='center',weight='bold')

# The complete BC547 enable circuits, with continuous wires from PCF to loads.
wire('AMP_CTL',[(1070,2200),(1370,2200)])
resistor('R16','100k',(1370,2200),(1450,2200),'AMP_CTL','Q1_BASE')
wire('Q1_BASE',[(1450,2200),(1500,2200)])
resistor('R15','100k',(1250,2280),(1250,2200),'3V3','AMP_CTL',label_side=-1);dot(1250,2200,'AMP_CTL')
wire('3V3',[(1250,2280),(1250,2310)],C['V3']);flag('3V3',1250,2320,C['V3'])
npn('Q1',1500,2200,'Q1_BASE','AMP_EN');ground(1540,2290,start=(1540,2240))
wire('AMP_EN',[(1540,2160),(1750,2160)])
resistor('R17','22k',(1540,2050),(1540,2130),'3V3','AMP_EN',label_side=-1)
wire('AMP_EN',[(1540,2130),(1540,2160)]);dot(1540,2160,'AMP_EN')
wire('3V3',[(1540,2050),(1540,2025)],C['V3']);flag('3V3',1540,2010,C['V3'])
wire('DRV_CTL',[(1070,2270),(1140,2270),(1140,2580),(2800,2580),(2800,2350),(2850,2350)])
resistor('R19','100k',(2850,2350),(2940,2350),'DRV_CTL','Q2_BASE')
wire('Q2_BASE',[(2940,2350),(3000,2350)])
resistor('R18','100k',(2800,2250),(2800,2350),'3V3','DRV_CTL',label_side=-1);dot(2800,2350,'DRV_CTL')
wire('3V3',[(2800,2250),(2800,2215)],C['V3']);flag('3V3',2800,2200,C['V3'])
npn('Q2',3000,2350,'Q2_BASE','DRIVER_EN');ground(3040,2440,start=(3040,2390))
wire('DRIVER_EN',[(3040,2310),(3240,2310),(3240,1870),(2570,1870),(2570,1650)])
resistor('R20','22k',(3140,2200),(3140,2310),'3V3','DRIVER_EN');dot(3140,2310,'DRIVER_EN')
wire('3V3',[(3140,2200),(3140,2165)],C['V3']);flag('3V3',3140,2150,C['V3'])
wire('FAULT',[(1070,2340),(1100,2340),(1100,2640),(2750,2640),(2750,1650)])
wire('FAULT',[(2750,2100),(2800,2100)]);dot(2750,2100,'FAULT')
resistor('R21','10k',(2800,2100),(2890,2100),'FAULT','3V3');wire('3V3',[(2890,2100),(2940,2100)],C['V3']);flag('3V3',2940,2100,C['V3'])
text(2950,1750,'Remove conflicting SLP/SD straps on carriers.\nPCF high/released → Q on → load disabled.\nPCF low → Q off → load enabled.',12,ha='center')
text(3050,2515,'Q1 / Q2: confirm actual B / C / E pinout.\nDo not substitute a transistor by body shape alone.',11,ha='center')

# Compact reading notes in the free left margin, not substitutes for components.
text(70,1290,'HOW TO READ THIS SHEET',15,weight='bold')
legend=[('VBAT / VM',C['VBAT']),('3V3 / local pull-up rail',C['V3']),('I²C SDA',C['SDA']),('I²C SCL',C['SCL']),('Motor PWM',C['motor']),('Audio I²S',C['audio']),('Touch',C['touch']),('Bumper',C['bumper']),('Enable / fault',C['ctl'])]
for i,(label,col) in enumerate(legend):
    yy=1340+i*44;ax.plot([70,145],[yy,yy],c=col,lw=2.5,zorder=5);text(165,yy,label,12)
text(70,1815,'ALL MODULE PINS ARE NAMED',14,weight='bold')
text(70,1885,'Follow the board silkscreen, not the drawing’s\nleft-to-right pin order. Rectangles are module\nsymbols; lines terminate at labelled pins.',12)
text(70,2005,'SENSOR CARRIER CHECK (*)',14,weight='bold')
text(70,2110,'VIN must accept 3.3 V. Do not feed a regulator\noutput. VIO_L/R/C = verified I²C pull-up rail.\nVLOGIC_L/R/C = actual sensor logic supply\n(often 2.8 V). A shifted SDA/SCL interface\ndoes not prove XSHUT is shifted.',12)
text(70,2250,'R23–R34 marked *: fit only when the correct\ncarrier pull-up is absent / bus checks require it.\nXSHUT: no extra wire if correctly pulled up on-board.\nGPIO1 unused. Robu carrier schematic unverified.',12)
text(70,2395,'CAMERA + MICROPHONE (ONBOARD)',14,weight='bold')
text(70,2495,'Mic CLK/DATA = GPIO42/41; retain J1/J2.\nCamera: XCLK10, PCLK13, VSYNC38, HREF47;\nSCCB SDA40/SCL39; D0–D7 =\n15,17,18,16,14,12,11,48. No extra jumpers.\nRemove SD card; isolate matching J3 pull-ups\nfor D8–D10 after checking board revision.',11)
text(1800,2710,'C1/C5 electrolytics: ≥10 V, observe polarity. Keep motor/audio returns away from sensors. All required carrier IC decoupling stays fitted.',12,ha='center')
text(1800,2750,'Mount all three sensors downward and calibrate before enabling motion. Hardware acceptance pending. Full pin/value list: docs/CIRCUIT.md',12,ha='center',weight='bold')

# Crossings are automatic: the horizontal wire hops over a different-net vertical.
# Same-net crossings receive a junction dot; collinear overlaps of different nets
# are errors and cannot silently produce a misleading diagram.
def between(v,a,b,strict=False):
    lo,hi=sorted((a,b))
    return lo < v < hi if strict else lo <= v <= hi

bridges={}
for i,(n,a,b,col,lw) in enumerate(segments):
    for n2,c,d,col2,lw2 in segments[i+1:]:
        hor=a[1]==b[1];hor2=c[1]==d[1]
        if hor==hor2:
            if hor and a[1]==c[1]:
                overlap=min(max(a[0],b[0]),max(c[0],d[0]))-max(min(a[0],b[0]),min(c[0],d[0]))
            elif not hor and a[0]==c[0]:
                overlap=min(max(a[1],b[1]),max(c[1],d[1]))-max(min(a[1],b[1]),min(c[1],d[1]))
            else:continue
            assert overlap<0 or n==n2, f'Overlapping/touching different nets: {n} {a,b} / {n2} {c,d}'
            continue
        h1,h2,v1,v2,hnet,vnet,hcol,hlw=(a,b,c,d,n,n2,col,lw) if hor else (c,d,a,b,n2,n,col2,lw2)
        x,y=v1[0],h1[1]
        if between(x,h1[0],h2[0]) and between(y,v1[1],v2[1]):
            if hnet==vnet:dot(x,y,hnet)
            else:
                assert between(x,h1[0],h2[0],True) and between(y,v1[1],v2[1],True), f'Different-net endpoint collision at {x,y}: {hnet}/{vnet}'
                bridges[(x,y)]=(hcol,hlw)
for (x,y),(col,lw) in bridges.items():
    ax.plot([x-9,x+9],[y,y],c='white',lw=lw+3,zorder=8,solid_capstyle='butt')
    ax.add_patch(Arc((x,y),18,18,theta1=180,theta2=360,ec='white',lw=lw+3,zorder=8))
    ax.add_patch(Arc((x,y),18,18,theta1=180,theta2=360,ec=col,lw=lw,zorder=9))
for x,y,net in set(junctions):
    assert (x,y) not in bridges, f'Junction conflicts with crossing: {x,y}'
    ax.add_patch(Circle((x,y),4.3,fc=C.get(net,C['ctl']),ec='none',zorder=10))

# Every component terminal must have an actual matching wire at its coordinate.
# This catches omitted capacitor, ground and module pin leads during redraws.
for key,p in pins.items():
    if p['net']=='NC':continue
    x,y=p['xy'];hits=[]
    for n,a,b,*_ in segments:
        if (a[0]==b[0]==x and between(y,a[1],b[1])) or (a[1]==b[1]==y and between(x,a[0],b[0])):hits.append(n)
    assert p['net'] in hits, f'Unwired terminal: {key} {p}'
    assert set(hits)=={p['net']}, f'Wrong net touches terminal: {key} {hits}'

# No wire may run through a module body or through a passive symbol's body.
# A resistor/capacitor is not a junction; crossing its body would be misleading.
for net,a,b,*_ in segments:
    for ref,x,y,w,h in boxes:
        if a[1]==b[1]:
            inside=y<a[1]<y+h and min(max(a[0],b[0]),x+w)>max(min(a[0],b[0]),x)
        else:
            inside=x<a[0]<x+w and min(max(a[1],b[1]),y+h)>max(min(a[1],b[1]),y)
        assert not inside, f'Wire {net} runs through module {ref}'
for ref in sorted({key.split('.')[0] for key in pins if key.startswith(('R','C','F1'))}):
    if f'{ref}.1' not in pins or f'{ref}.2' not in pins:continue
    a=pins[f'{ref}.1']['xy'];b=pins[f'{ref}.2']['xy']
    for net,c,d,*_ in segments:
        if a[0]==b[0] and c[1]==d[1]:
            hits=between(c[1],a[1],b[1],True) and between(a[0],c[0],d[0])
        elif a[1]==b[1] and c[0]==d[0]:
            hits=between(c[0],a[0],b[0],True) and between(a[1],c[1],d[1])
        elif a[0]==b[0]==c[0]==d[0]:
            hits=min(max(a[1],b[1]),max(c[1],d[1]))>max(min(a[1],b[1]),min(c[1],d[1]))
        elif a[1]==b[1]==c[1]==d[1]:
            hits=min(max(a[0],b[0]),max(c[0],d[0]))>max(min(a[0],b[0]),min(c[0],d[0]))
        else:hits=False
        assert not hits, f'Wire {net} crosses the body of {ref}'

# Export one master and three crops of the same drawing, not separate designs.
OUT.mkdir(exist_ok=True)
views=[('bob-wiring',(0,0,W,H)),
       ('bob-circuit-1',(1300,180,3550,1740)),
       ('bob-circuit-2',(25,225,1360,2570)),
       ('bob-circuit-3',(1300,860,3550,2680))]
for name,(x0,y0,x1,y1) in views:
    ax.set(xlim=(x0,x1),ylim=(y1,y0))
    fig.set_size_inches((x1-x0)/100,(y1-y0)/100)
    for ext in ('svg','png'):
        file=OUT/f'{name}.{ext}'
        fig.savefig(file,dpi=160,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
        if ext=='svg':file.write_text('\n'.join(row.rstrip() for row in file.read_text().splitlines())+'\n')
plt.close(fig)
netlist={}
for key,p in sorted(pins.items()):
    if p['net']!='NC':netlist.setdefault(p['net'],[]).append(key)
(ROOT/'docs/circuit-netlist.json').write_text(json.dumps({'description':'Revision 3.2 drawing; external module terminal nets. Physical header order is not implied.', 'nets':netlist,'unconnected':[k for k,v in pins.items() if v['net']=='NC']},indent=2)+'\n')
print(f'PASS: {len(pins)} terminals checked; {len(netlist)} named nets; {len(bridges)} unjoined crossings. Exported master + 3 detail views.')
