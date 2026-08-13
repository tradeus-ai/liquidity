import pandas as pd
from market_structure import MarketStructureAnalyzer

df = pd.read_parquet('data/AUDUSD_1d.parquet')
ms = MarketStructureAnalyzer(df)
res = ms.identify_structure()
events = res.dropna(subset=['structure_event'])
events_apr = events[events.index.astype(str).str.contains('2026-04')]
print("1D Events:")
print(events_apr[['close', 'high', 'low', 'structure_event']])

df = pd.read_parquet('data/AUDUSD_15m.parquet')
ms = MarketStructureAnalyzer(df)
res = ms.identify_structure()
events = res.dropna(subset=['structure_event'])
events_apr = events[events.index.astype(str).str.contains('2026-04-17')]
print("\n15M Events:")
print(events_apr[['close', 'high', 'low', 'structure_event']])
