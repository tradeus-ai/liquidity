import pandas as pd
from smartmoneyconcepts import smc
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
df = tv.get_hist(symbol="NIFTY", exchange="NSE", interval=Interval.in_15_minute, n_bars=1000)
swings = smc.swing_highs_lows(df)
print(swings.dropna().tail(10))
