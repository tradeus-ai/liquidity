"""
SMC Pullback Module
===================

This module implements Smart Money Concepts (SMC) pullback logic to identify
swing highs and swing lows on OHLC candlestick data.

Concept
-------
A "pullback" in SMC is a candle-by-candle structure that determines the 
directional flow of the market by comparing against reference Mother Bars.

Rules
-----
1. HIGH BROKEN (curr_high > ref_high OR curr_open > ref_high):
   - Market direction is UP.
   - If previously DOWN, a swing LOW is confirmed at the lowest point of the DOWN leg.

2. LOW BROKEN (curr_low < ref_low OR curr_open < ref_low):
   - Market direction is DOWN.
   - If previously UP, a swing HIGH is confirmed at the highest point of the UP leg.

3. OUTSIDE BAR (curr_high > ref_high AND curr_low < ref_low):
   - If curr_open > ref_high or curr_open < ref_low, the open price itself broke that side FIRST.
   - Otherwise, we use LTF data (15m/5m) to see which side was broken FIRST.
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
    logger.info("SMC PULLBACK SWING DETECTION STARTED (Mother Bar & Open Break Logic)")
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
    
    ref_high = df['high'].iloc[0]
    ref_low = df['low'].iloc[0]
    ref_date = df.index[0]
    
    for i in range(1, len(df)):
        date = df.index[i]
        curr_open = df['open'].iloc[i]
        curr_high = df['high'].iloc[i]
        curr_low = df['low'].iloc[i]
        
        # Check if open or high/low broke the reference Mother Bar
        open_broke_high = curr_open > ref_high
        open_broke_low = curr_open < ref_low
        
        broke_high = (curr_high > ref_high) or open_broke_high
        broke_low = (curr_low < ref_low) or open_broke_low
        
        if broke_high and broke_low:
            logger.info(f"[{date}] OUTSIDE BAR | Prev {ref_date} H={ref_high:.2f} L={ref_low:.2f}")
            
            taken_first = None
            
            # Rule: If open price itself gaps above ref_high or below ref_low, that side was broken first at open!
            if open_broke_high:
                taken_first = 'HIGH'
                logger.info(f"  🔍 Open gap break: Open={curr_open:.2f} > ref_H={ref_high:.2f} -> HIGH taken first at open")
            elif open_broke_low:
                taken_first = 'LOW'
                logger.info(f"  🔍 Open gap break: Open={curr_open:.2f} < ref_L={ref_low:.2f} -> LOW taken first at open")
                
            # Rule 2: Open price proximity logic (|curr_open - ref_high| vs |curr_open - ref_low|)
            if not taken_first:
                dist_to_high = abs(curr_open - ref_high)
                dist_to_low = abs(curr_open - ref_low)
                if dist_to_low < dist_to_high:
                    taken_first = 'LOW'
                    logger.info(f"  🔍 Open proximity: dist_L={dist_to_low:.2f} < dist_H={dist_to_high:.2f} -> LOW taken first (Open={curr_open:.2f})")
                elif dist_to_high < dist_to_low:
                    taken_first = 'HIGH'
                    logger.info(f"  🔍 Open proximity: dist_H={dist_to_high:.2f} < dist_L={dist_to_low:.2f} -> HIGH taken first (Open={curr_open:.2f})")
                    
            if not taken_first and ltf_df is not None and not ltf_df.empty:
                next_date = df.index[i + 1] if i + 1 < len(df) else None
                mask = (ltf_df.index >= date) & (ltf_df.index < next_date) if next_date else (ltf_df.index >= date)
                ltf_candles = ltf_df.loc[mask]
                for _, row in ltf_candles.iterrows():
                    h_break = row['high'] > ref_high
                    l_break = row['low'] < ref_low
                    if h_break and l_break:
                        if row['open'] > ref_high:
                            taken_first = 'HIGH'
                        elif row['open'] < ref_low:
                            taken_first = 'LOW'
                        else:
                            taken_first = 'HIGH' if row['close'] >= row['open'] else 'LOW'
                        logger.info(f"  🔍 LTF resolved (15m outside bar): {taken_first} taken first at {row.name}")
                        break
                    elif h_break:
                        taken_first = 'HIGH'
                        logger.info(f"  🔍 LTF resolved: HIGH taken first at {row.name}")
                        break
                    elif l_break:
                        taken_first = 'LOW'
                        logger.info(f"  🔍 LTF resolved: LOW taken first at {row.name}")
                        break
            
            if not taken_first:
                # Fallback if LTF not available or no break found: align with active trend
                taken_first = 'HIGH' if current_dir == 1 else 'LOW'
                logger.info(f"  🔍 Trend fallback: {taken_first} first based on active trend ({current_dir})")
            
            if taken_first == 'HIGH':
                # Process HIGH break, then LOW break
                process_up_break(i, curr_high)
                process_down_break(i, curr_low)
            else:
                # Process LOW break, then HIGH break
                process_down_break(i, curr_low)
                process_up_break(i, curr_high)
                
            # Update reference candle
            ref_high = curr_high
            ref_low = curr_low
            ref_date = date
                
        else:
            # Normal logic: explicitly branch on trend direction
            if current_dir == 1:
                # In an UP trend, we look for the low to be broken to form a swing high
                if broke_low:
                    reason = "OPEN GAP LOW" if open_broke_low else "LOW BROKEN"
                    logger.debug(f"[{date}] {reason} (Trend Reverse) | Prev {ref_date}")
                    process_down_break(i, curr_low)
                    ref_high = curr_high
                    ref_low = curr_low
                    ref_date = date
                elif broke_high:
                    reason = "OPEN GAP HIGH" if open_broke_high else "HIGH BROKEN"
                    logger.debug(f"[{date}] {reason} (Trend Continue) | Prev {ref_date}")
                    process_up_break(i, curr_high)
                    ref_high = curr_high
                    ref_low = curr_low
                    ref_date = date
                else:
                    logger.debug(f"[{date}] INSIDE BAR | Prev {ref_date}")
                    
            elif current_dir == -1:
                # In a DOWN trend, we look for the high to be broken to form a swing low
                if broke_high:
                    reason = "OPEN GAP HIGH" if open_broke_high else "HIGH BROKEN"
                    logger.debug(f"[{date}] {reason} (Trend Reverse) | Prev {ref_date}")
                    process_up_break(i, curr_high)
                    ref_high = curr_high
                    ref_low = curr_low
                    ref_date = date
                elif broke_low:
                    reason = "OPEN GAP LOW" if open_broke_low else "LOW BROKEN"
                    logger.debug(f"[{date}] {reason} (Trend Continue) | Prev {ref_date}")
                    process_down_break(i, curr_low)
                    ref_high = curr_high
                    ref_low = curr_low
                    ref_date = date
                else:
                    logger.debug(f"[{date}] INSIDE BAR | Prev {ref_date}")
                    
            else:
                # Neutral (start of chart)
                if broke_high:
                    process_up_break(i, curr_high)
                    ref_high = curr_high
                    ref_low = curr_low
                    ref_date = date
                elif broke_low:
                    process_down_break(i, curr_low)
                    ref_high = curr_high
                    ref_low = curr_low
                    ref_date = date
                else:
                    logger.debug(f"[{date}] INSIDE BAR | Prev {ref_date}")
            
    total_highs = df['is_swing_high'].sum()
    total_lows = df['is_swing_low'].sum()
    logger.info("=" * 80)
    logger.info(f"SWING DETECTION COMPLETE | Highs: {total_highs} | Lows: {total_lows}")
    logger.info("=" * 80)
    
    return df
