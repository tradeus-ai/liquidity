from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
df = tv.get_hist(symbol='AUDUSD', exchange='PEPPERSTONE', interval=Interval.in_4_hour, n_bars=1000)
print(len(df) if df is not None else "Failed")
