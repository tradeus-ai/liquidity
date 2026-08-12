from structure_service import get_chart_data
import pandas as pd

data = get_chart_data('AXISBANK', '1d', 'futures')
df = pd.DataFrame(data['candles'])
df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
print("OHLC Data for AXISBANK (Late July):")
print(df[(df['time'] >= '2026-07-22') & (df['time'] <= '2026-07-31')][['time', 'open', 'high', 'low', 'close']].to_string(index=False))
