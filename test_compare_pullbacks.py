from structure_service import get_chart_data
import pandas as pd

# Fetch Python SMC pullbacks
data = get_chart_data('AXISBANK', '1d', 'futures')
pullback_points = data.get('pullback_points', [])
python_pts = {p['time'][:10]: p['value'] for p in pullback_points}

# Print the points between May and August to see where they differ
print("Python Pullback Points (May-August 2026):")
for p in pullback_points:
    if '2026-05-01' <= p['time'] <= '2026-08-15':
        print(f"{p['time'][:10]} | {p['value']:.2f}")
