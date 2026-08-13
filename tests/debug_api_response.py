"""Check the actual JSON response the browser would receive."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from structure_service import get_chart_data
import pandas as pd

data = get_chart_data('AXISBANK', '1d', 'futures')
pp = data.get('pullback_points', [])

print(f"Total pullback_points: {len(pp)}")
print("\n=== Pullback points July 22 - Aug 5 ===")
for i, p in enumerate(pp):
    t = str(p['time'])
    if '2026-07-22' <= t[:10] <= '2026-08-05':
        print(f"  [{i}] time='{p['time']}' value={p['value']:.2f}")

# Check for duplicated timestamps
times = [p['time'] for p in pp]
dupes = set()
seen = set()
for t in times:
    if t in seen:
        dupes.add(t)
    seen.add(t)
    
if dupes:
    print(f"\n*** DUPLICATED TIMESTAMPS FOUND: {dupes} ***")
    print("LightweightCharts will SILENTLY DROP duplicated timestamps!")
    for i, p in enumerate(pp):
        if p['time'] in dupes:
            print(f"  [{i}] time='{p['time']}' value={p['value']:.2f}")
else:
    print("\nNo duplicated timestamps found.")
    
# Also check monotonic time order
non_mono = []
for i in range(1, len(pp)):
    if pp[i]['time'] <= pp[i-1]['time']:
        non_mono.append((i, pp[i-1], pp[i]))
        
if non_mono:
    print(f"\n*** NON-MONOTONIC TIMESTAMPS FOUND ({len(non_mono)}) ***")
    for idx, prev, cur in non_mono[:10]:
        print(f"  [{idx}] prev={prev['time']} ({prev['value']:.2f}) -> cur={cur['time']} ({cur['value']:.2f})")
else:
    print("All timestamps are monotonically increasing.")
