from smc_pullback import find_swings
from data_fetcher import DataFetcher
from tvDatafeed import Interval

fetcher = DataFetcher()
df = fetcher.fetch_data('ABB', 'NSE', Interval.in_daily, '1d')
df = find_swings(df)

sh_count = df['is_swing_high'].sum()
sl_count = df['is_swing_low'].sum()

print(f"Total Swing Highs: {sh_count}, Total Swing Lows: {sl_count}")
print("\nLast 10 Swings:")
swings = df[df['is_swing_high'] | df['is_swing_low']]
for idx, row in swings.tail(10).iterrows():
    kind = "HIGH" if row['is_swing_high'] else "LOW"
    val = row['high'] if row['is_swing_high'] else row['low']
    print(f"{idx} | {kind} | {val}")
