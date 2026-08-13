# Temporary script to analyze gaps in ABB futures data
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import sys

tv = TvDatafeed()
df = tv.get_hist(symbol='ABB1!', exchange='NSE', interval=Interval.in_daily, n_bars=200)

if df is not None:
    df['gap_up'] = df['open'] > df['close'].shift(1) * 1.005 # 0.5% gap
    df['gap_down'] = df['open'] < df['close'].shift(1) * 0.995
    print("Gap Ups:", len(df[df['gap_up']]))
    print("Gap Downs:", len(df[df['gap_down']]))
