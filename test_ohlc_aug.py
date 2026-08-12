from structure_service import get_chart_data
import pandas as pd

data = get_chart_data('AXISBANK', '1d', 'futures')
df = pd.DataFrame(data['candles'])
df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
print("OHLC Data for AXISBANK (Early August):")
print(df[(df['time'] >= '2026-08-01') & (df['time'] <= '2026-08-07')][['time', 'open', 'high', 'low', 'close']].to_string(index=False))
