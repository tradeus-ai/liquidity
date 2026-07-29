import pandas as pd
import datetime

t = "2024-05-01"
ts = int(pd.to_datetime(t).timestamp())
print(ts)
print(datetime.datetime.utcfromtimestamp(ts))
