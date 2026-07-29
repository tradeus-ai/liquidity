import pandas as pd
import numpy as np
from smc_pullback import find_swings

def test_logic():
    df = pd.read_parquet('data/AMBUJACEM1_bang_1d.parquet')
    df = find_swings(df)
    
    # We want to see if we can extract active_pb_high immediately
    proper_high_idx = pd.Timestamp('2018-09-03')
    idx = pd.Timestamp('2018-10-31')
    
    cycle_start_idx = proper_high_idx
    proper_low_idx = idx
    
    sub_df = df.loc[cycle_start_idx:proper_low_idx]
    sh_rows = sub_df[sub_df['is_swing_high'] == True]
    if len(sh_rows) > 0:
        print(f"Found active_pb_high: {sh_rows.index[-1].strftime('%Y-%m-%d')} val={sh_rows['high'].iloc[-1]}")
    else:
        print("No active_pb_high found")

test_logic()
