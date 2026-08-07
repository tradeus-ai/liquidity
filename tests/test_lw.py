import pandas as pd
from lightweight_charts.widgets import StaticLWC

chart = StaticLWC()
df = pd.DataFrame({
    'time': ['2023-01-01', '2023-01-02'],
    'open': [100, 105], 'high': [110, 115], 'low': [90, 95], 'close': [105, 110]
})
chart.set(df)
line = chart.trend_line('2023-01-01', 105, '2023-01-02', 110, line_color='red')
line.run_script(f"{line.id}.applyOptions({{text: 'TEST LABEL'}})")
html = chart._html
with open('test.html', 'w') as f:
    f.write(html)
