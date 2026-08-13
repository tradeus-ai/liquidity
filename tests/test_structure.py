from structure_service import get_chart_data

data = get_chart_data('AUDUSD', timeframe_raw='15m', market_type='forex')
print(f"Events: {len(data['htf_events'])}")
print(f"Zones: {len(data['zones'])}")
