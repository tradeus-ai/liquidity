import pandas as pd
import numpy as np
from smc_pullback import find_swings

df = pd.read_parquet('data/AMBUJACEM1_bang_1d.parquet')
df = find_swings(df)

# Let's look at the Case 1 leg
# IDM triggered on 2018-04-18, breaking 2018-03-15 SH (val=246.00)
# Proper Low was 2018-03-23 (val=223.00)
leg = df.loc['2018-03-15':'2018-04-18']
print(leg[['open','high','low','close','is_swing_high','is_swing_low']])
