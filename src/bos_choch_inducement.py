"""
BOS, ChoCH and Inducement Module for Higher Timeframe (Daily 1D)
===============================================================

This module implements Smart Money Concepts (SMC) Market Structure:
1. Inducement (#): First pullback low broken in uptrend (first pullback high in downtrend), located PRIOR TO / LEFT OF the peak high / low but WITHIN the current structure cycle.
2. Proper High / Low: Confirmed once Inducement occurs.
3. Break of Structure (BOS): Candle CLOSE above Proper High (or below Proper Low). Wicks are ignored until candle closes above wick high.
4. Inducement Shift (IS): Subsequent inducement prior to candle closure above proper high.
5. Change of Character (ChoCH): Major structural high/low break that flips trend.

RULE: BOS can NEVER occur without a preceding Inducement in the same cycle.
"""

import pandas as pd
import numpy as np
from zone_service import ZoneManager



def analyze_htf_structure(df):
    """
    Analyzes Daily (1D) dataframe with identified pullback swings (is_swing_high, is_swing_low)
    and returns a list of structure event dicts for drawing lines/markers on chart.
    """
    df = df.copy()
    if len(df) < 5:
        return []
    structure_events = []
    zm = ZoneManager(0.003, enabled=True)

    
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
    
    wick_high_idx = None
    wick_high_val = None
    wick_low_idx = None
    wick_low_val = None
    
    choch_idx = min_low_idx
    choch_val = min_low_val
    
    # Track cycle start — the candle where the current trend cycle began
    # Inducement levels must only come from swing points AFTER this boundary
    cycle_start_idx = min_low_idx
    
    for i in range(min_low_i, len(df)):
        idx = df.index[i]
        c_high = float(df['high'].iloc[i])
        c_low = float(df['low'].iloc[i])
        c_close = float(df['close'].iloc[i])
        is_sh = df['is_swing_high'].iloc[i]
        is_sl = df['is_swing_low'].iloc[i]
        
        # Mitigate existing zones with current candle
        zm.process_candle(idx, c_low, c_high)
        
        # We loop up to 2 times to allow a ChoCH on this candle to immediately 
        # trigger the new trend's Inducement/BOS logic on the same candle.
        event_triggered_this_candle = False
        trends_processed = 0
        while trends_processed < 2:
            if event_triggered_this_candle:
                break
            prev_trend = current_trend
            
            if current_trend == 1:
                if proper_high_val is None:
                    if is_sh:
                        proper_high_idx = idx
                        proper_high_val = c_high
                    # Don't break here, we still need to check choch
                else:
                    if not inducement_done:
                        # Update peak high and find last swing low WITHIN current cycle and PRIOR TO this peak
                        if c_high >= proper_high_val:
                            proper_high_idx = idx
                            proper_high_val = c_high
                            
                            # Only look for swing lows AFTER cycle_start_idx
                            sub_df = df.loc[cycle_start_idx:proper_high_idx].iloc[:-1]
                            sl_rows = sub_df[sub_df['is_swing_low'] == True]
                            if len(sl_rows) > 0:
                                active_pb_low_idx = sl_rows.index[-1]
                                active_pb_low_val = float(sl_rows['low'].iloc[-1])
                            else:
                                active_pb_low_idx = None
                                active_pb_low_val = None
                                
                        # Check Inducement (#): Low breaks valid pullback low within current cycle
                        if active_pb_low_val is not None and c_low < active_pb_low_val:
                            inducement_done = True
                            label = "#"
                            evt_type = "IDM"
                            event_triggered_this_candle = True
                            
                            structure_events.append({
                                'type': evt_type,
                                'label': label,
                                'start_time': active_pb_low_idx,
                                'start_val': active_pb_low_val,
                                'end_time': idx,
                                'end_val': active_pb_low_val,
                                'color': '#ffd600'
                            })
                            
                            # Uptrend Confirmed: Identify Demand Zones
                            if evt_type == 'IDM':
                                zm.handle_idm_uptrend(df, choch_idx, proper_high_idx, active_pb_low_idx)

                    else:
                        if wick_high_val is not None:
                            # Check for Inducement Shift (IS)
                            # IS pullback low must be prior to the wick high (left of the high)
                            sub_df = df.loc[cycle_start_idx:wick_high_idx].iloc[:-1]
                            sl_rows = sub_df[sub_df['is_swing_low'] == True]
                            if len(sl_rows) > 0:
                                current_pb_low_idx = sl_rows.index[-1]
                                current_pb_low_val = float(sl_rows['low'].iloc[-1])
                            else:
                                current_pb_low_idx = None
                                current_pb_low_val = None
                                
                            if current_pb_low_val is not None and c_low < current_pb_low_val:
                                old_proper_high_idx = proper_high_idx
                                # IS occurred! The wick high is now confirmed as the new proper high.
                                proper_high_idx = wick_high_idx
                                proper_high_val = wick_high_val
                                event_triggered_this_candle = True
                                
                                structure_events.append({
                                    'type': 'IS',
                                    'label': 'IS',
                                    'start_time': current_pb_low_idx,
                                    'start_val': current_pb_low_val,
                                    'end_time': idx,
                                    'end_val': current_pb_low_val,
                                    'color': '#00e5ff'
                                })
                                
                                # NEW REQUIREMENT: draw zones on the left side of inducement shift
                                zm.handle_is_uptrend(df, choch_idx, old_proper_high_idx, proper_high_idx, current_pb_low_idx)
                                
                                wick_high_idx = None
                                wick_high_val = None
                                
                        target_high = wick_high_val if wick_high_val is not None else proper_high_val
                        
                        # Check BOS: Candle CLOSE above Proper High / Wick High
                        if c_close > target_high:
                            event_triggered_this_candle = True
                            structure_events.append({
                                'type': 'BOS',
                                'label': 'BOS',
                                'start_time': proper_high_idx,
                                'start_val': proper_high_val,
                                'end_time': idx,
                                'end_val': proper_high_val,
                                'color': '#2962ff'
                            })
                            zm.clear_on_bos(idx)
                            # Lowest low in this BOS leg becomes the new ChoCH level
                            leg_df = df.loc[proper_high_idx:idx]
                            leg_min_i = leg_df['low'].idxmin()
                            choch_idx = leg_min_i
                            choch_val = float(leg_df.loc[leg_min_i, 'low'])
                            
                            inducement_done = False
                            wick_high_idx = None
                            wick_high_val = None
                            proper_high_idx = idx
                            proper_high_val = c_high
                            # Fetch active pullback for the new leg immediately
                            sub_df = df.loc[cycle_start_idx:proper_high_idx].iloc[:-1]
                            sl_rows = sub_df[sub_df['is_swing_low'] == True]
                            if len(sl_rows) > 0:
                                active_pb_low_idx = sl_rows.index[-1]
                                active_pb_low_val = float(sl_rows['low'].iloc[-1])
                            else:
                                active_pb_low_idx = None
                                active_pb_low_val = None
                            
                        # Wick break: High > target but Close <= target
                        elif c_high > target_high and c_close <= target_high:
                            wick_high_idx = idx
                            wick_high_val = c_high
                            # IS check happens on next candles
                                
                # Check ChoCH: Low breaks structural ChoCH level
                if choch_val is not None and c_low < choch_val:
                    event_triggered_this_candle = True
                    structure_events.append({
                        'type': 'CHOCH',
                        'label': 'ChoCH',
                        'start_time': choch_idx,
                        'start_val': choch_val,
                        'end_time': idx,
                        'end_val': choch_val,
                        'color': '#e91e63'
                    })
                    # Clear all active zones on ChoCH
                    zm.clear_on_choch(idx)
                    
                    current_trend = -1
                    proper_low_idx = idx
                    proper_low_val = c_low
                    inducement_done = False
                    wick_high_idx = None
                    wick_high_val = None
                    choch_idx = proper_high_idx
                    choch_val = proper_high_val
                    # New cycle starts here (from peak high)
                    cycle_start_idx = proper_high_idx
                    # Fetch active pullback for the new leg immediately
                    sub_df = df.loc[cycle_start_idx:proper_low_idx].iloc[:-1]
                    sh_rows = sub_df[sub_df['is_swing_high'] == True]
                    if len(sh_rows) > 0:
                        active_pb_high_idx = sh_rows.index[-1]
                        active_pb_high_val = float(sh_rows['high'].iloc[-1])
                    else:
                        active_pb_high_idx = None
                        active_pb_high_val = None

            elif current_trend == -1:
                if proper_low_val is None:
                    if is_sl:
                        proper_low_idx = idx
                        proper_low_val = c_low
                    # Don't break here, we still need to check choch
                else:
                    if not inducement_done:
                        # Update peak low and find last swing high WITHIN current cycle and PRIOR TO this peak
                        if c_low <= proper_low_val:
                            proper_low_idx = idx
                            proper_low_val = c_low
                            
                            # Only look for swing highs AFTER cycle_start_idx
                            sub_df = df.loc[cycle_start_idx:proper_low_idx].iloc[:-1]
                            sh_rows = sub_df[sub_df['is_swing_high'] == True]
                            if len(sh_rows) > 0:
                                active_pb_high_idx = sh_rows.index[-1]
                                active_pb_high_val = float(sh_rows['high'].iloc[-1])
                            else:
                                active_pb_high_idx = None
                                active_pb_high_val = None
                                
                        # Check Inducement (#): High breaks valid pullback high within current cycle
                        if active_pb_high_val is not None and c_high > active_pb_high_val:
                            inducement_done = True
                            label = "#"
                            evt_type = "IDM"
                            event_triggered_this_candle = True
                            
                            structure_events.append({
                                'type': evt_type,
                                'label': label,
                                'start_time': active_pb_high_idx,
                                'start_val': active_pb_high_val,
                                'end_time': idx,
                                'end_val': active_pb_high_val,
                                'color': '#ffd600'
                            })
                            
                            # Downtrend Confirmed: Identify Supply Zones
                            if evt_type == 'IDM':
                                zm.handle_idm_downtrend(df, choch_idx, proper_low_idx, active_pb_high_idx)

                    else:
                        if wick_low_val is not None:
                            # Check for Inducement Shift (IS)
                            # IS pullback high must be prior to the wick low (left of the low)
                            sub_df = df.loc[cycle_start_idx:wick_low_idx].iloc[:-1]
                            sh_rows = sub_df[sub_df['is_swing_high'] == True]
                            if len(sh_rows) > 0:
                                current_pb_high_idx = sh_rows.index[-1]
                                current_pb_high_val = float(sh_rows['high'].iloc[-1])
                            else:
                                current_pb_high_idx = None
                                current_pb_high_val = None
                                
                            if current_pb_high_val is not None and c_high > current_pb_high_val:
                                old_proper_low_idx = proper_low_idx
                                # IS occurred! The wick low is now confirmed as the new proper low.
                                proper_low_idx = wick_low_idx
                                proper_low_val = wick_low_val
                                event_triggered_this_candle = True
                                
                                structure_events.append({
                                    'type': 'IS',
                                    'label': 'IS',
                                    'start_time': current_pb_high_idx,
                                    'start_val': current_pb_high_val,
                                    'end_time': idx,
                                    'end_val': current_pb_high_val,
                                    'color': '#00e5ff'
                                })
                                
                                # NEW REQUIREMENT: draw zones on the left side of inducement shift
                                zm.handle_is_downtrend(df, choch_idx, old_proper_low_idx, proper_low_idx, current_pb_high_idx)
                                
                                wick_low_idx = None
                                wick_low_val = None
                                
                        target_low = wick_low_val if wick_low_val is not None else proper_low_val
                        
                        # Check BOS: Candle CLOSE below Proper Low / Wick Low
                        if c_close < target_low:
                            event_triggered_this_candle = True
                            structure_events.append({
                                'type': 'BOS',
                                'label': 'BOS',
                                'start_time': proper_low_idx,
                                'start_val': proper_low_val,
                                'end_time': idx,
                                'end_val': proper_low_val,
                                'color': '#2962ff'
                            })
                            zm.clear_on_bos(idx)
                            # Highest high in this BOS leg becomes the new ChoCH level
                            leg_df = df.loc[proper_low_idx:idx]
                            leg_max_i = leg_df['high'].idxmax()
                            choch_idx = leg_max_i
                            choch_val = float(leg_df.loc[leg_max_i, 'high'])
                            
                            inducement_done = False
                            wick_low_idx = None
                            wick_low_val = None
                            proper_low_idx = idx
                            proper_low_val = c_low
                            # Fetch active pullback for the new leg immediately
                            sub_df = df.loc[cycle_start_idx:proper_low_idx].iloc[:-1]
                            sh_rows = sub_df[sub_df['is_swing_high'] == True]
                            if len(sh_rows) > 0:
                                active_pb_high_idx = sh_rows.index[-1]
                                active_pb_high_val = float(sh_rows['high'].iloc[-1])
                            else:
                                active_pb_high_idx = None
                                active_pb_high_val = None
                            
                        # Wick break: Low < target but Close >= target
                        elif c_low < target_low and c_close >= target_low:
                            wick_low_idx = idx
                            wick_low_val = c_low
                            # IS check happens on next candles
                                
                # Check ChoCH: High breaks structural ChoCH level
                if choch_val is not None and c_high > choch_val:
                    event_triggered_this_candle = True
                    structure_events.append({
                        'type': 'CHOCH',
                        'label': 'ChoCH',
                        'start_time': choch_idx,
                        'start_val': choch_val,
                        'end_time': idx,
                        'end_val': choch_val,
                        'color': '#e91e63'
                    })
                    # Clear all active zones on ChoCH
                    zm.clear_on_choch(idx)
                    
                    current_trend = 1
                    proper_high_idx = idx
                    proper_high_val = c_high
                    inducement_done = False
                    wick_low_idx = None
                    wick_low_val = None
                    choch_idx = proper_low_idx
                    choch_val = proper_low_val
                    # New cycle starts here (from peak low)
                    cycle_start_idx = proper_low_idx
                    # Fetch active pullback for the new leg immediately
                    sub_df = df.loc[cycle_start_idx:proper_high_idx].iloc[:-1]
                    sl_rows = sub_df[sub_df['is_swing_low'] == True]
                    if len(sl_rows) > 0:
                        active_pb_low_idx = sl_rows.index[-1]
                        active_pb_low_val = float(sl_rows['low'].iloc[-1])
                    else:
                        active_pb_low_idx = None
                        active_pb_low_val = None
            
            if current_trend == prev_trend:
                break
            trends_processed += 1
    
    # Finalize remaining active zones
    if len(df) > 0:
        last_idx = df.index[-1]
        zm.finalize(last_idx)
            
    return {
        'events': structure_events,
        'zones': zm.get_all_zones(),
        'current_state': {
            'trend': current_trend,
            'inducement_done': inducement_done
        }
    }

