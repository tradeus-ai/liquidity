import pandas as pd
from market_structure import MarketStructureAnalyzer

# Synthetic data
# Uptrend scenario where a single candle drops and sweeps BOTH IDM and ChoCH
data = [
    {'time': '2026-04-10', 'open': 1.0, 'high': 2.0, 'low': 0.5, 'close': 1.5, 'volume': 100}, # Bar 0
    {'time': '2026-04-11', 'open': 1.5, 'high': 3.0, 'low': 1.0, 'close': 2.5, 'volume': 100}, # Bar 1 (New High)
    {'time': '2026-04-12', 'open': 2.5, 'high': 2.6, 'low': 2.0, 'close': 2.4, 'volume': 100}, # Bar 2 (Inside Bar / Pullback)
    {'time': '2026-04-13', 'open': 2.4, 'high': 4.0, 'low': 2.1, 'close': 3.5, 'volume': 100}, # Bar 3 (Breaks high, confirms swing low at Bar 2)
    {'time': '2026-04-14', 'open': 3.5, 'high': 3.6, 'low': 3.2, 'close': 3.3, 'volume': 100}, # Bar 4
    {'time': '2026-04-15', 'open': 3.3, 'high': 3.4, 'low': 3.1, 'close': 3.2, 'volume': 100}, # Bar 5 (Pullback low)
    {'time': '2026-04-16', 'open': 3.2, 'high': 5.0, 'low': 3.1, 'close': 4.5, 'volume': 100}, # Bar 6 (Breaks high, confirm swing low at Bar 5. New High at Bar 6)
    
    # At this point:
    # Proper High = 5.0 (Bar 6)
    # IDM level = 3.1 (Bar 5 low)
    # ChoCH level = 2.0 (Bar 2 low, or 1.0 depending on swing structure)
    
    # 2026-04-17: Massive drop that sweeps IDM (3.1) AND ChoCH (2.0)
    {'time': '2026-04-17', 'open': 4.5, 'high': 4.6, 'low': 1.5, 'close': 1.8, 'volume': 100}, # Bar 7
]

df = pd.DataFrame(data)
analyzer = MarketStructureAnalyzer(df)
res = analyzer.identify_structure()

print(res[['time', 'structure_event', 'market_high', 'market_low']])
