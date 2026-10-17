#!/usr/bin/env python3
"""Capture USB status without moving the robot; never uploads or unlocks."""
import argparse
import json
from pathlib import Path
import time

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True, help='COM5 or /dev/cu.usbmodem...')
    parser.add_argument('--seconds',type=float,default=30)
    parser.add_argument('--output',type=Path,default=Path('build/bench.jsonl'))
    args=parser.parse_args()
    import serial
    args.output.parent.mkdir(parents=True,exist_ok=True)
    count=0; worst=0; moving=False
    with serial.Serial(args.port,115200,timeout=.2) as device, args.output.open('w') as out:
        device.write(b'stop\n')
        end=time.monotonic()+args.seconds; last=0
        while time.monotonic()<end:
            if time.monotonic()-last>.2:
                device.write(b'status\n'); last=time.monotonic()
            line=device.readline(4096).decode(errors='replace').strip()
            try: row=json.loads(line)
            except (ValueError,TypeError): continue
            if not isinstance(row,dict) or row.get('type')!='status': continue
            row['host_time']=time.time(); out.write(json.dumps(row)+'\n'); out.flush()
            count+=1; worst=max(worst,row.get('cycle_ms',0)); moving|=row.get('moving',False)
        device.write(b'stop\n')
    print(f'{count} samples; worst cycle {worst} ms; file: {args.output}')
    if not count or moving or worst>=120: raise SystemExit('FAIL: missing telemetry, unexpected movement, or sensor deadline exceeded')
    print('Capture PASS. This does not certify physical stopping distance or electrical safety.')

if __name__=='__main__': main()
