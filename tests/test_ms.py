import pandas as pd
from market_structure import MarketStructureAnalyzer

try:
    df = pd.read_parquet('data/AUDUSD_15m.parquet')
    ms = MarketStructureAnalyzer(df)
    res = ms.identify_structure()
    events = res.dropna(subset=['structure_event'])
    
    # Filter events for April 2026
    events_apr = events[events.index.astype(str).str.contains('2026-04')]
    print(events_apr[['close', 'high', 'low', 'structure_event']])
    
    print("ALL APRIL 2026 EVENTS:")
    for idx, row in events_apr.iterrows():
        print(f"{idx}: {row['structure_event']}")
except Exception as e:
    print(f"Error: {e}")
