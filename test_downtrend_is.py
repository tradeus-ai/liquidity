import pandas as pd
from bos_choch_inducement import analyze_htf_structure

# Create a mock dataframe for a downtrend
data = {
    'time': pd.date_range('2023-01-01', periods=10),
    'open':  [100, 98, 95, 105, 100, 100, 110, 120, 100, 90],
    'high':  [105, 100, 110, 120, 110, 105, 130, 125, 105, 100],
    'low':   [95,  90,  94,  100, 95,  85,  105, 115, 95,  80],
    'close': [98,  95,  105, 115, 105, 102, 120, 118, 90,  85],
    'is_swing_high': [False, False, False, True, False, False, False, False, False, False],
    'is_swing_low':  [False, True, False, False, False, False, False, False, False, False]
}
df = pd.DataFrame(data).set_index('time')

events = analyze_htf_structure(df)
print("Events:", events)
