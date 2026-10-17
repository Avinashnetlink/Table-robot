#!/usr/bin/env python3
"""Propose ToF desk bands from stopped firmware captures; never edits config or arms."""
import argparse
import json
from pathlib import Path

def load(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    rows = [r for r in rows if isinstance(r, dict) and r.get('type') == 'status']
    if len(rows) < 20:
        raise ValueError('capture at least 20 status samples for each surface')
    for row in rows:
        if row.get('moving') is not False or row.get('unlocked') is not False:
            raise ValueError('calibrate only while motion is locked and stopped')
        for name in ('edge_mm', 'edge_valid', 'edge_status'):
            if not isinstance(row.get(name), list) or len(row[name]) != 3:
                raise ValueError('requires revision 3 telemetry with all three sensors')
        if any(type(v) is not int or not 0 <= v <= 65535 for v in row['edge_mm']):
            raise ValueError('invalid distance data')
        if any(type(v) is not bool for v in row['edge_valid']):
            raise ValueError('invalid validity data')
        if any(type(v) is not int or not 0 <= v <= 15 for v in row['edge_status']):
            raise ValueError('I2C/mux fault or stale data: repair before calibration')
    return rows

def propose(desk, air, margin=5):
    if not 3 <= margin <= 20:
        raise ValueError('margin must be 3..20 mm')
    models = {r.get('edge_sensor') for r in desk + air}
    if len(models) != 1 or not models <= {'VL6180X', 'VL53L0X'}:
        raise ValueError('captures must use the same supported sensor family')
    if any(not all(r['edge_valid']) for r in desk):
        raise ValueError('invalid desk reading: adjust mounting or reject this surface')
    lo = [max(1, min(r['edge_mm'][i] for r in desk)-margin) for i in range(3)]
    hi = [max(r['edge_mm'][i] for r in desk)+margin for i in range(3)]
    if 'VL6180X' in models and max(hi) > 100:
        raise ValueError('VL6180X desk band must remain within 100 mm')
    if any(hi[i]-lo[i] <= 6 for i in range(3)):
        raise ValueError('insufficient band for 3 mm reacquisition hysteresis')
    for row in air:
        for i in range(3):
            if row['edge_valid'][i] and lo[i] <= row['edge_mm'][i] <= hi[i]:
                raise ValueError(f'air overlaps desk band on sensor {i}; unsafe geometry')
    return lo, hi

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--desk', required=True, type=Path)
    p.add_argument('--air', required=True, type=Path)
    p.add_argument('--margin-mm', type=int, default=5)
    args=p.parse_args()
    try:
        lo, hi=propose(load(args.desk), load(args.air), args.margin_mm)
    except (ValueError, OSError) as exc:
        p.exit(1, f'FAIL: {exc}\n')
    for name, values in (('EDGE_MIN_MM',lo),('EDGE_MAX_MM',hi)):
        print(f'constexpr uint16_t {name}[3] = {{{", ".join(map(str,values))}}};')
    print('Candidate only. Repeat across surfaces/lighting and measure physical stopping margin. Motion remains locked.')

if __name__=='__main__': main()
