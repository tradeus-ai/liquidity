import sys
sys.path.append('.')
from structure_service import get_chart_data

data = get_chart_data('NIFTY', '1d', 'futures')
if 'error' in data:
    print("Error:", data['error'])
else:
    events = data.get('htf_events', [])
    print("Events found:", len(events))
    is_events = [e for e in events if e['label'] == 'IS']
    print("IS Events found:", len(is_events))
