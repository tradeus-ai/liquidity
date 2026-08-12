from datetime import timedelta
import pandas as pd

dt = pd.to_datetime('2026-07-29')
print(dt.strftime('%Y-%m-%d'))
print((dt + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'))
