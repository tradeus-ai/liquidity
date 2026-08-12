import json
from structure_service import get_chart_data

data = get_chart_data('ABB', '1d', 'futures')
events = data.get('htf_events', [])
for ev in events:
    print(ev['type'], ev['start_time'], ev['end_time'], ev['end_val'])
