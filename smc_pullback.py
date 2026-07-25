"""
SMC Pullback Module
===================

This module implements Smart Money Concepts (SMC) pullback logic to identify
swing highs and swing lows on OHLC candlestick data.

Concept
-------
A "pullback" in SMC is a candle-by-candle structure that determines the 
directional flow of the market by ALWAYS comparing the current candle against
the IMMEDIATELY PREVIOUS candle (no Mother Bar logic).

Rules
-----
1. HIGH BROKEN (curr_high > prev_high):
   - Market direction is UP.
   - If previously DOWN, a swing LOW is confirmed at the lowest point of the DOWN leg.

2. LOW BROKEN (curr_low < prev_low):
   - Market direction is DOWN.
   - If previously UP, a swing HIGH is confirmed at the highest point of the UP leg.

3. OUTSIDE BAR (curr_high > prev_high AND curr_low < prev_low):
   - We use the 15m timeframe (if available) to see which was broken FIRST.
   - If 15m isn't available, we use the opening price trick:
     distance_to_high = abs(curr_open - prev_high)
     distance_to_low  = abs(curr_open - prev_low)
     Whichever is smaller was taken FIRST.
   - Once we know what was broken first, we process the outside bar as TWO 
     SEQUENTIAL breaks. 
     Example: If HIGH was taken first, we process the HIGH break, then the LOW break.
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger('smc_pullback')

def find_swings(df, ltf_df=None):
    df = df.copy()
    df['is_swing_high'] = False
    df['is_swing_low'] = False
    
    if len(df) < 2:
        return df
        
    current_dir = 0  # 0=neutral, 1=UP, -1=DOWN
    
    swing_high_idx = 0
    swing_high_val = df['high'].iloc[0]
    swing_low_idx = 0
    swing_low_val = df['low'].iloc[0]
    
    logger.info("=" * 80)
    logger.info("SMC PULLBACK SWING DETECTION STARTED (Previous Candle Logic)")
    logger.info("=" * 80)
    
    def process_up_break(i, high_val):
        nonlocal current_dir, swing_high_idx, swing_high_val, swing_low_idx, swing_low_val
        if current_dir == -1:
            # DOWN -> UP
            df.loc[df.index[swing_low_idx], 'is_swing_low'] = True
            logger.info(f"  ✅ SWING LOW CONFIRMED at {df.index[swing_low_idx]} | Low={swing_low_val:.2f}")
            current_dir = 1
            swing_high_idx = i
            swing_high_val = high_val
        elif current_dir == 1:
            # Continue UP
            if high_val >= swing_high_val:
                swing_high_idx = i
                swing_high_val = high_val
        else:
            current_dir = 1
            swing_high_idx = i
            swing_high_val = high_val

    def process_down_break(i, low_val):
        nonlocal current_dir, swing_high_idx, swing_high_val, swing_low_idx, swing_low_val
        if current_dir == 1:
            # UP -> DOWN
            df.loc[df.index[swing_high_idx], 'is_swing_high'] = True
            logger.info(f"  ✅ SWING HIGH CONFIRMED at {df.index[swing_high_idx]} | High={swing_high_val:.2f}")
            current_dir = -1
            swing_low_idx = i
            swing_low_val = low_val
        elif current_dir == -1:
            # Continue DOWN
            if low_val <= swing_low_val:
                swing_low_idx = i
                swing_low_val = low_val
        else:
            current_dir = -1
            swing_low_idx = i
            swing_low_val = low_val
    
    for i in range(1, len(df)):
        date = df.index[i]
        curr_open = df['open'].iloc[i]
        curr_high = df['high'].iloc[i]
        curr_low = df['low'].iloc[i]
        
        prev_high = df['high'].iloc[i-1]
        prev_low = df['low'].iloc[i-1]
        prev_date = df.index[i-1]
        
        broke_high = curr_high > prev_high
        broke_low = curr_low < prev_low
        
        if broke_high and broke_low:
            logger.info(f"[{date}] OUTSIDE BAR | Prev {prev_date} H={prev_high:.2f} L={prev_low:.2f}")
            
            taken_first = None
            if ltf_df is not None and not ltf_df.empty:
                next_date = df.index[i + 1] if i + 1 < len(df) else None
                mask = (ltf_df.index >= date) & (ltf_df.index < next_date) if next_date else (ltf_df.index >= date)
                ltf_candles = ltf_df.loc[mask]
                for _, row in ltf_candles.iterrows():
                    if row['high'] > prev_high:
                        taken_first = 'HIGH'
                        logger.info(f"  🔍 LTF resolved: HIGH taken first at {row.name}")
                        break
                    if row['low'] < prev_low:
                        taken_first = 'LOW'
                        logger.info(f"  🔍 LTF resolved: LOW taken first at {row.name}")
                        break
            
            if not taken_first:
                dist_to_high = abs(curr_open - prev_high)
                dist_to_low = abs(curr_open - prev_low)
                if dist_to_high <= dist_to_low:
                    taken_first = 'HIGH'
                    logger.info(f"  🔍 Open trick: dist_H={dist_to_high:.2f} <= dist_L={dist_to_low:.2f} -> HIGH first")
                else:
                    taken_first = 'LOW'
                    logger.info(f"  🔍 Open trick: dist_L={dist_to_low:.2f} < dist_H={dist_to_high:.2f} -> LOW first")
            
            if taken_first == 'HIGH':
                # Process HIGH break, then LOW break
                process_up_break(i, curr_high)
                process_down_break(i, curr_low)
            else:
                # Process LOW break, then HIGH break
                process_down_break(i, curr_low)
                process_up_break(i, curr_high)
                
        elif broke_high:
            logger.debug(f"[{date}] HIGH BROKEN | Prev {prev_date}")
            process_up_break(i, curr_high)
                
        elif broke_low:
            logger.debug(f"[{date}] LOW BROKEN | Prev {prev_date}")
            process_down_break(i, curr_low)
                
        else:
            logger.debug(f"[{date}] INSIDE BAR | Prev {prev_date}")
            
    total_highs = df['is_swing_high'].sum()
    total_lows = df['is_swing_low'].sum()
    logger.info("=" * 80)
    logger.info(f"SWING DETECTION COMPLETE | Highs: {total_highs} | Lows: {total_lows}")
    logger.info("=" * 80)
    
    return df
