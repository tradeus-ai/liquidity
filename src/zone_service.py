"""
Zone Service Module
===================

Dedicated service for Supply & Demand Zone drawing, extraction, shaving, mitigation,
and structural lifecycle management (BOS/ChoCH invalidation).
Extracted as a separate service for easier debugging and modular testing.
"""

import pandas as pd
import numpy as np


def add_zone(active_zones, start_time, bottom, top, peak, zone_type, threshold=0.003):
    # Try to merge with an existing zone
    for z in active_zones:
        diff = abs(z['peak'] - peak) / z['peak']
        if diff <= threshold:
            z['bottom'] = min(z['bottom'], bottom)
            z['top'] = max(z['top'], top)
            z['start_time'] = start_time
            z['history'].append({'time': start_time, 'top': z['top'], 'bottom': z['bottom']})
            return
            
    active_zones.append({
        'start_time': start_time,
        'bottom': bottom,
        'top': top,
        'peak': peak,
        'type': zone_type,
        'history': [{'time': start_time, 'top': top, 'bottom': bottom}]
    })


def merge_zones(raw_zones, threshold=0.003):
    if not raw_zones:
        return []
    raw_zones = sorted(raw_zones, key=lambda x: x['start_time'])
    merged = []
    current = dict(raw_zones[0])
    for next_zone in raw_zones[1:]:
        diff = abs(current['peak'] - next_zone['peak']) / current['peak']
        if diff <= threshold:
            current['bottom'] = min(current['bottom'], next_zone['bottom'])
            current['top'] = max(current['top'], next_zone['top'])
            current['start_time'] = next_zone['start_time']
        else:
            merged.append(current)
            current = dict(next_zone)
    merged.append(current)
    for z in merged:
        z['history'] = [{'time': z['start_time'], 'top': z['top'], 'bottom': z['bottom']}]
    return merged


def extract_demand_zones(df, cycle_start_idx, proper_high_idx, active_pb_low_idx, threshold=0.003):
    leg_df = df.loc[cycle_start_idx:proper_high_idx]
    sl_rows = leg_df[leg_df['is_swing_low'] == True]
    sl_rows = sl_rows[sl_rows.index < active_pb_low_idx]
    
    valid_zones = []
    for z_idx, row in sl_rows.iterrows():
        zone_bottom = float(row['low'])
        
        # Rule 6 (Option C): Top is the previous swing high peak
        prev_df = leg_df.loc[:z_idx]
        prev_df = prev_df.iloc[:-1] if len(prev_df) > 0 else prev_df
        prev_sh = prev_df[prev_df['is_swing_high'] == True]
        if len(prev_sh) > 0:
            zone_top = float(prev_sh['high'].iloc[-1])
        else:
            zone_top = float(prev_df['high'].max()) if len(prev_df) > 0 else float(row['high'])
        peak = zone_bottom
        
        # Gap logic: if next candle gaps up, the gap itself becomes the zone
        idx_pos = df.index.get_loc(z_idx)
        if idx_pos + 1 < len(df):
            next_candle = df.iloc[idx_pos + 1]
            if next_candle['low'] > zone_top:
                zone_bottom = zone_top
                zone_top = float(next_candle['low'])
        
        # Check if the zone was mitigated in the future of this leg
        future_df = leg_df.loc[z_idx:]
        future_df = future_df.iloc[1:] # exclude the swing low bar itself
        
        mitigated = False
        if len(future_df) > 0:
            lowest_future = future_df['low'].min()
            if lowest_future <= zone_bottom:
                mitigated = True
            else:
                # If pierced but not broken, shave the top down
                touches = future_df[future_df['low'] < zone_top]
                if len(touches) > 0:
                    zone_top = float(touches['low'].min())
                    
        if not mitigated:
            valid_zones.append({
                'start_time': z_idx,
                'bottom': zone_bottom,
                'top': zone_top,
                'peak': zone_bottom,
                'type': 'demand'
            })
            
    return merge_zones(valid_zones, threshold)


def extract_supply_zones(df, cycle_start_idx, proper_low_idx, active_pb_high_idx, threshold=0.003):
    leg_df = df.loc[cycle_start_idx:proper_low_idx]
    sh_rows = leg_df[leg_df['is_swing_high'] == True]
    sh_rows = sh_rows[sh_rows.index < active_pb_high_idx]
    
    valid_zones = []
    for z_idx, row in sh_rows.iterrows():
        zone_top = float(row['high'])
        
        # Rule 7 (Option C): Bottom is the previous swing low trough
        prev_df = leg_df.loc[:z_idx]
        prev_df = prev_df.iloc[:-1] if len(prev_df) > 0 else prev_df
        prev_sl = prev_df[prev_df['is_swing_low'] == True]
        if len(prev_sl) > 0:
            zone_bottom = float(prev_sl['low'].iloc[-1])
        else:
            zone_bottom = float(prev_df['low'].min()) if len(prev_df) > 0 else float(row['low'])
            
        peak = zone_top
        
        # Gap logic: if next candle gaps down, the gap itself becomes the zone
        idx_pos = df.index.get_loc(z_idx)
        if idx_pos + 1 < len(df):
            next_candle = df.iloc[idx_pos + 1]
            if next_candle['high'] < zone_bottom:
                zone_top = zone_bottom
                zone_bottom = float(next_candle['high'])
        
        # Check if the zone was mitigated in the future of this leg
        future_df = leg_df.loc[z_idx:]
        future_df = future_df.iloc[1:] # exclude the swing high bar itself
        
        mitigated = False
        if len(future_df) > 0:
            highest_future = future_df['high'].max()
            if highest_future >= zone_top:
                mitigated = True
            else:
                # If pierced but not broken, shave the bottom up
                touches = future_df[future_df['high'] > zone_bottom]
                if len(touches) > 0:
                    zone_bottom = float(touches['high'].max())
                    
        if not mitigated:
            valid_zones.append({
                'start_time': z_idx,
                'bottom': zone_bottom,
                'top': zone_top,
                'peak': zone_top,
                'type': 'supply'
            })
            
    return merge_zones(valid_zones, threshold)


class ZoneManager:
    """
    Manages active and historical Supply & Demand zones throughout structure analysis.
    Handles extraction on IDM / IS, bar-by-bar mitigation & shaving, and invalidation on BOS / ChoCH.
    """
    def __init__(self, threshold=0.003, enabled=False):
        self.threshold = threshold
        self.enabled = enabled
        self.active_demand_zones = []
        self.active_supply_zones = []
        self.historical_zones = []

    def process_candle(self, idx, c_low, c_high):
        """Processes real-time mitigation and shaving for active demand and supply zones."""
        if not self.enabled:
            return
        # Demand Zones (touched if low dips into top)
        for z in self.active_demand_zones[:]:
            if idx > z['start_time'] and c_low < z['top']:
                if c_low <= z['bottom']:
                    z['end_time'] = idx
                    z['status'] = 'mitigated'
                    self.historical_zones.append(z)
                    self.active_demand_zones.remove(z)
                else:
                    z['top'] = c_low
                    z['history'].append({'time': idx, 'top': z['top'], 'bottom': z['bottom']})
                    
        # Supply Zones (touched if high pierces bottom)
        for z in self.active_supply_zones[:]:
            if idx > z['start_time'] and c_high > z['bottom']:
                if c_high >= z['top']:
                    z['end_time'] = idx
                    z['status'] = 'mitigated'
                    self.historical_zones.append(z)
                    self.active_supply_zones.remove(z)
                else:
                    z['bottom'] = c_high
                    z['history'].append({'time': idx, 'top': z['top'], 'bottom': z['bottom']})

    def handle_idm_uptrend(self, df, choch_idx, proper_high_idx, active_pb_low_idx):
        """Extracts demand zones when Inducement occurs in an uptrend."""
        if not self.enabled:
            return
        merged = extract_demand_zones(df, choch_idx, proper_high_idx, active_pb_low_idx, self.threshold)
        self.active_demand_zones.extend(merged)

    def handle_is_uptrend(self, df, old_proper_high_idx, proper_high_idx, current_pb_low_idx):
        """Extracts demand zones when Inducement Shift occurs in an uptrend."""
        if not self.enabled:
            return
        merged = extract_demand_zones(df, old_proper_high_idx, proper_high_idx, current_pb_low_idx, self.threshold)
        self.active_demand_zones.extend(merged)

    def handle_idm_downtrend(self, df, choch_idx, proper_low_idx, active_pb_high_idx):
        """Extracts supply zones when Inducement occurs in a downtrend."""
        if not self.enabled:
            return
        merged = extract_supply_zones(df, choch_idx, proper_low_idx, active_pb_high_idx, self.threshold)
        self.active_supply_zones.extend(merged)

    def handle_is_downtrend(self, df, old_proper_low_idx, proper_low_idx, current_pb_high_idx):
        """Extracts supply zones when Inducement Shift occurs in a downtrend."""
        if not self.enabled:
            return
        merged = extract_supply_zones(df, old_proper_low_idx, proper_low_idx, current_pb_high_idx, self.threshold)
        self.active_supply_zones.extend(merged)

    def clear_on_bos(self, idx):
        """Invalidates all active zones upon Break of Structure (BOS)."""
        for z in self.active_demand_zones:
            z['end_time'] = idx
            z['status'] = 'invalidated_by_bos'
            self.historical_zones.append(z)
        self.active_demand_zones.clear()

        for z in self.active_supply_zones:
            z['end_time'] = idx
            z['status'] = 'invalidated_by_bos'
            self.historical_zones.append(z)
        self.active_supply_zones.clear()

    def clear_on_choch(self, idx):
        """Invalidates all active zones upon Change of Character (ChoCH)."""
        for z in self.active_demand_zones:
            z['end_time'] = idx
            z['status'] = 'invalidated_by_choch'
            self.historical_zones.append(z)
        self.active_demand_zones.clear()

        for z in self.active_supply_zones:
            z['end_time'] = idx
            z['status'] = 'invalidated_by_choch'
            self.historical_zones.append(z)
        self.active_supply_zones.clear()

    def finalize(self, last_idx):
        """Finalizes active zones at dataset end."""
        for z in self.active_demand_zones:
            z['end_time'] = last_idx
            z['status'] = 'active'
            self.historical_zones.append(z)
        for z in self.active_supply_zones:
            z['end_time'] = last_idx
            z['status'] = 'active'
            self.historical_zones.append(z)

    def get_all_zones(self):
        """Returns all tracked zones (active + historical)."""
        return self.historical_zones
