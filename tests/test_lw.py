import pandas as pd
from lightweight_charts import Chart

if __name__ == '__main__':
    chart = Chart()
    
    df = pd.DataFrame({
        'time': ['2026-07-24', '2026-07-29', '2026-08-03', '2026-08-05'],
        'open': [1200, 1220, 1230, 1260],
        'high': [1215, 1245, 1265, 1270],
        'low': [1190, 1210, 1225, 1255],
        'close': [1210, 1235, 1250, 1265]
    })
    
    # Convert df time to unix
    df['time'] = pd.to_datetime(df['time']).astype('int64') // 10**9
    
    chart.set(df)
    
    line = chart.create_line(color='#ff9800', width=3)
    line_df = pd.DataFrame([
        {'time': pd.to_datetime('2026-07-24').timestamp(), 'value': 1190},
        {'time': pd.to_datetime('2026-07-29').timestamp(), 'value': 1245},
        {'time': pd.to_datetime('2026-07-29').timestamp() + 1, 'value': 1210},
        {'time': pd.to_datetime('2026-08-03').timestamp(), 'value': 1265},
        {'time': pd.to_datetime('2026-08-03').timestamp() + 1, 'value': 1225},
        {'time': pd.to_datetime('2026-08-05').timestamp(), 'value': 1270}
    ])
    
    try:
        line.set(line_df)
        print("Success with unix timestamps offset")
    except Exception as e:
        print(f"Error with offset: {e}")
