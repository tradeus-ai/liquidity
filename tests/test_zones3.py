from structure_service import get_chart_data

data = get_chart_data('ABB', '1d', 'futures')
zones = data.get('htf_zones', [])
print("Total zones returned:", len(zones))
for z in zones:
    print(z['type'], z['start_time'], z['end_time'], z['status'])
