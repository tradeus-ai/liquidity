"""
BOS, ChoCH and Inducement Module for Higher Timeframe (Daily 1D)
===============================================================

This module implements Smart Money Concepts (SMC) Market Structure:
1. Inducement (#): First pullback low broken in uptrend (first pullback high in downtrend), located PRIOR TO / LEFT OF the peak high / low.
2. Proper High / Low: Confirmed once Inducement occurs.
3. Break of Structure (BOS): Candle CLOSE above Proper High (or below Proper Low). Wicks are ignored until candle closes above wick high.
4. Inducement Shift (IS): Subsequent inducement prior to candle closure above proper high.
5. Change of Character (ChoCH): Major structural high/low break that flips trend.
"""

import pandas as pd
import numpy as np

def analyze_htf_structure(df):
    """
    Analyzes Daily (1D) dataframe with identified pullback swings (is_swing_high, is_swing_low)
    and returns a list of structure event dicts for drawing lines/markers on chart.
    """
    df = df.copy()
    if len(df) < 5:
        return []

    structure_events = []
    
    # 1 = UPTREND, -1 = DOWNTREND
    current_trend = 1
    
    # Start structure cycle from the lowest low in the dataset
    min_low_i = int(np.argmin(df['low'].values))
    min_low_idx = df.index[min_low_i]
    min_low_val = float(df['low'].iloc[min_low_i])
    
    proper_high_idx = None
    proper_high_val = None
    proper_low_idx = None
    proper_low_val = None
    
    inducement_done = False
    active_pb_low_idx = None
    active_pb_low_val = None
    active_pb_high_idx = None
    active_pb_high_val = None
    
    wick_high_val = None
    wick_low_val = None
    
    choch_idx = min_low_idx
    choch_val = min_low_val
    
    for i in range(min_low_i, len(df)):
        idx = df.index[i]
        c_high = float(df['high'].iloc[i])
        c_low = float(df['low'].iloc[i])
        c_close = float(df['close'].iloc[i])
        is_sh = df['is_swing_high'].iloc[i]
        is_sl = df['is_swing_low'].iloc[i]
        
        if current_trend == 1:
            if proper_high_val is None:
                if is_sh:
                    proper_high_idx = idx
                    proper_high_val = c_high
                continue
                
            if not inducement_done:
                # Update peak high and find last swing low PRIOR TO this peak high
                if c_high >= proper_high_val:
                    proper_high_idx = idx
                    proper_high_val = c_high
                    
                    sub_df = df.loc[:proper_high_idx]
                    sl_rows = sub_df[sub_df['is_swing_low'] == True]
                    if len(sl_rows) > 0:
                        active_pb_low_idx = sl_rows.index[-1]
                        active_pb_low_val = float(sl_rows['low'].iloc[-1])
                    else:
                        active_pb_low_idx = None
                        active_pb_low_val = None
                        
                # Check Inducement (#): Low breaks valid pullback low prior to proper high
                if active_pb_low_val is not None and c_low < active_pb_low_val:
                    inducement_done = True
                    label = "IS" if wick_high_val is not None else "#"
                    evt_type = "IS" if wick_high_val is not None else "IDM"
                    
                    structure_events.append({
                        'type': evt_type,
                        'label': label,
                        'start_time': active_pb_low_idx,
                        'start_val': active_pb_low_val,
                        'end_time': idx,
                        'end_val': active_pb_low_val,
                        'color': '#00e5ff' if evt_type == 'IS' else '#ffd600'
                    })
            else:
                target_high = wick_high_val if wick_high_val is not None else proper_high_val
                
                # Check BOS: Candle CLOSE above Proper High / Wick High
                if c_close > target_high:
                    structure_events.append({
                        'type': 'BOS',
                        'label': 'BOS',
                        'start_time': proper_high_idx,
                        'start_val': proper_high_val,
                        'end_time': idx,
                        'end_val': proper_high_val,
                        'color': '#2962ff'
                    })
                    # Lowest low in this BOS leg becomes the new ChoCH level
                    leg_df = df.loc[proper_high_idx:idx]
                    leg_min_i = leg_df['low'].idxmin()
                    choch_idx = leg_min_i
                    choch_val = float(leg_df.loc[leg_min_i, 'low'])
                    
                    inducement_done = False
                    wick_high_val = None
                    proper_high_idx = idx
                    proper_high_val = c_high
                    
                # Wick break: High > target but Close <= target
                elif c_high > target_high and c_close <= target_high:
                    wick_high_val = c_high
                    sub_df = df.loc[:idx]
                    sl_rows = sub_df[sub_df['is_swing_low'] == True]
                    if len(sl_rows) > 0:
                        active_pb_low_idx = sl_rows.index[-1]
                        active_pb_low_val = float(sl_rows['low'].iloc[-1])
                        
            # Check ChoCH: Low breaks structural ChoCH level
            if choch_val is not None and c_low < choch_val:
                structure_events.append({
                    'type': 'CHOCH',
                    'label': 'ChoCH',
                    'start_time': choch_idx,
                    'start_val': choch_val,
                    'end_time': idx,
                    'end_val': choch_val,
                    'color': '#e91e63'
                })
                current_trend = -1
                proper_low_idx = idx
                proper_low_val = c_low
                inducement_done = False
                wick_high_val = None
                choch_idx = proper_high_idx
                choch_val = proper_high_val

        elif current_trend == -1:
            if proper_low_val is None:
                if is_sl:
                    proper_low_idx = idx
                    proper_low_val = c_low
                continue
                
            if not inducement_done:
                # Update peak low and find last swing high PRIOR TO this peak low
                if c_low <= proper_low_val:
                    proper_low_idx = idx
                    proper_low_val = c_low
                    
                    sub_df = df.loc[:proper_low_idx]
                    sh_rows = sub_df[sub_df['is_swing_high'] == True]
                    if len(sh_rows) > 0:
                        active_pb_high_idx = sh_rows.index[-1]
                        active_pb_high_val = float(sh_rows['high'].iloc[-1])
                    else:
                        active_pb_high_idx = None
                        active_pb_high_val = None
                        
                # Check Inducement (#): High breaks valid pullback high prior to proper low
                if active_pb_high_val is not None and c_high > active_pb_high_val:
                    inducement_done = True
                    label = "IS" if wick_low_val is not None else "#"
                    evt_type = "IS" if wick_low_val is not None else "IDM"
                    
                    structure_events.append({
                        'type': evt_type,
                        'label': label,
                        'start_time': active_pb_high_idx,
                        'start_val': active_pb_high_val,
                        'end_time': idx,
                        'end_val': active_pb_high_val,
                        'color': '#00e5ff' if evt_type == 'IS' else '#ffd600'
                    })
            else:
                target_low = wick_low_val if wick_low_val is not None else proper_low_val
                
                # Check BOS: Candle CLOSE below Proper Low / Wick Low
                if c_close < target_low:
                    structure_events.append({
                        'type': 'BOS',
                        'label': 'BOS',
                        'start_time': proper_low_idx,
                        'start_val': proper_low_val,
                        'end_time': idx,
                        'end_val': proper_low_val,
                        'color': '#2962ff'
                    })
                    # Highest high in this BOS leg becomes the new ChoCH level
                    leg_df = df.loc[proper_low_idx:idx]
                    leg_max_i = leg_df['high'].idxmax()
                    choch_idx = leg_max_i
                    choch_val = float(leg_df.loc[leg_max_i, 'high'])
                    
                    inducement_done = False
                    wick_low_val = None
                    proper_low_idx = idx
                    proper_low_val = c_low
                    
                # Wick break: Low < target but Close >= target
                elif c_low < target_low and c_close >= target_low:
                    wick_low_val = c_low
                    sub_df = df.loc[:idx]
                    sh_rows = sub_df[sub_df['is_swing_high'] == True]
                    if len(sh_rows) > 0:
                        active_pb_high_idx = sh_rows.index[-1]
                        active_pb_high_val = float(sh_rows['high'].iloc[-1])
                        
            # Check ChoCH: High breaks structural ChoCH level
            if choch_val is not None and c_high > choch_val:
                structure_events.append({
                    'type': 'CHOCH',
                    'label': 'ChoCH',
                    'start_time': choch_idx,
                    'start_val': choch_val,
                    'end_time': idx,
                    'end_val': choch_val,
                    'color': '#e91e63'
                })
                current_trend = 1
                proper_high_idx = idx
                proper_high_val = c_high
                inducement_done = False
                wick_low_val = None
                choch_idx = proper_low_idx
                choch_val = proper_low_val

    return structure_events
