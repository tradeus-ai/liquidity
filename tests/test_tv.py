from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
df = tv.get_hist(symbol='AUDUSD', exchange='PEPPERSTONE', interval=Interval.in_daily, n_bars=5)
print(df)
