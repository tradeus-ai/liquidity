import pandas as pd
from tvDatafeed import TvDatafeed, Interval

def main():
    tv = TvDatafeed()
    
    symbol = 'AMBUJACEM1!'
    exchange = 'NSE'
    
    print(f"Fetching {symbol} 15m data...")
    df_15m = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_15_minute, n_bars=10)
    print(df_15m.head())
    print(f"Fetched {len(df_15m)} rows for 15m")
    
    print(f"Fetching {symbol} 1D data...")
    df_1d = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=5000)
    print(df_1d.head())
    print(f"Fetched {len(df_1d)} rows for 1D")

if __name__ == "__main__":
    main()
