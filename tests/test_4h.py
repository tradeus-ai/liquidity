from structure_service import get_chart_data

data = get_chart_data('AUDUSD', timeframe_raw='4h', market_type='forex')
print(f"4H Events: {len(data['htf_events'])}")
print(f"4H Zones: {len(data['zones'])}")
