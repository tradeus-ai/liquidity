from structure_service import get_chart_data
import pandas as pd

data = get_chart_data('AXISBANK', '1d', 'futures')
df = pd.DataFrame(data['candles'])
print(df.head())
dt = pd.to_datetime(df['time'].iloc[0])
print(dt)
print(int(dt.timestamp()))
