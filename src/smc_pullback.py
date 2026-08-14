"""
SMC Pullback Module
===================

This module implements Smart Money Concepts (SMC) pullback logic to identify
swing highs and swing lows on OHLC candlestick data.

It is 100% synchronized with Pine Script (tradeus_toolkit.pine).
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger('smc_pullback')




def find_swings(df, ltf_df=None, symbol=""):
    df = df.copy()
    df['is_swing_high'] = False
    df['is_swing_low'] = False
    
    if len(df) < 2:
        return df

    opens = df['open'].values.tolist()
    highs = df['high'].values.tolist()
    lows  = df['low'].values.tolist()

    current_dir = 0  # 0 = neutral, 1 = UP, -1 = DOWN
    swing_high_idx = 0
    swing_high_val = highs[0]
    swing_low_idx = 0
    swing_low_val = lows[0]

    ref_high = highs[0]
    ref_low = lows[0]

    def process_up_break(i, h_val):
        nonlocal current_dir, swing_high_idx, swing_high_val, swing_low_idx, swing_low_val
        if current_dir == -1:
            df.loc[df.index[swing_low_idx], 'is_swing_low'] = True
            current_dir = 1
            swing_high_idx = i
            swing_high_val = h_val
        elif current_dir == 1:
            if h_val >= swing_high_val:
                swing_high_idx = i
                swing_high_val = h_val
        else:
            current_dir = 1
            swing_high_idx = i
            swing_high_val = h_val

    def process_down_break(i, l_val):
        nonlocal current_dir, swing_high_idx, swing_high_val, swing_low_idx, swing_low_val
        if current_dir == 1:
            df.loc[df.index[swing_high_idx], 'is_swing_high'] = True
            current_dir = -1
            swing_low_idx = i
            swing_low_val = l_val
        elif current_dir == -1:
            if l_val <= swing_low_val:
                swing_low_idx = i
                swing_low_val = l_val
        else:
            current_dir = -1
            swing_low_idx = i
            swing_low_val = l_val

    for i in range(1, len(df)):
        curr_open = opens[i]
        curr_high = highs[i]
        curr_low  = lows[i]

        open_broke_high = curr_open > ref_high
        open_broke_low  = curr_open < ref_low

        broke_high = (curr_high > ref_high) or open_broke_high
        broke_low  = (curr_low < ref_low) or open_broke_low

        if broke_high or broke_low:
            if broke_high and broke_low:
                taken_first = 0
                if open_broke_high:
                    taken_first = 1
                elif open_broke_low:
                    taken_first = -1
                else:
                    dist_high = abs(curr_open - ref_high)
                    dist_low  = abs(curr_open - ref_low)
                    if dist_low < dist_high:
                        taken_first = -1
                    else:
                        taken_first = 1

                if taken_first == 1:
                    process_up_break(i, curr_high)
                    process_down_break(i, curr_low)
                else:
                    process_down_break(i, curr_low)
                    process_up_break(i, curr_high)
            else:
                if current_dir == 1:
                    if broke_low:
                        process_down_break(i, curr_low)
                    elif broke_high:
                        process_up_break(i, curr_high)
                elif current_dir == -1:
                    if broke_high:
                        process_up_break(i, curr_high)
                    elif broke_low:
                        process_down_break(i, curr_low)
                else:
                    if broke_high:
                        process_up_break(i, curr_high)
                    elif broke_low:
                        process_down_break(i, curr_low)

            # Update mother bar reference values
            ref_high = curr_high
            ref_low  = curr_low

    total_highs = df['is_swing_high'].sum()
    total_lows = df['is_swing_low'].sum()
    logger.info(f"SWING DETECTION COMPLETE | Highs: {total_highs} | Lows: {total_lows}")

    return df
