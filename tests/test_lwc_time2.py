import pandas as pd
from lightweight_charts.widgets import StaticLWC

df = pd.DataFrame({
    'time': pd.date_range('2026-07-21 09:15:00', periods=5, freq='15min'),
    'open': [100, 101, 102, 101, 100],
    'high': [102, 103, 104, 103, 102],
    'low': [99, 100, 101, 100, 99],
    'close': [101, 102, 101, 100, 101]
})

# Convert intraday index to unix timestamps (integer seconds)
df['time'] = df['time'].astype('int64') // 10**9

chart = StaticLWC()
chart.set(df)
t1 = df['time'].iloc[0]
t2 = df['time'].iloc[-1]
chart.trend_line(t1, 100, t2, 101, line_color='blue')
chart.load()
with open("test_lwc_time2.html", "w") as f:
    f.write(chart._html)
