from structure_service import get_chart_data
import pandas as pd

data = get_chart_data('AXISBANK', '1d', 'futures')
pullback_points = data.get('pullback_points', [])
print("Pullbacks:")
for p in pullback_points:
    if '2026-07-20' <= p['time'] <= '2026-08-05':
        print(f"{p['time']} | {p['value']:.2f}")

print("\nCandles:")
for c in data['candles']:
    if '2026-07-20' <= c['time'] <= '2026-08-05':
        print(c)
