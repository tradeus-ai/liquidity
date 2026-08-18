"""
Zone Service Module
===================

Dedicated service for Supply & Demand Zone drawing, extraction, mitigation,
and structural lifecycle management (BOS/ChoCH invalidation).

Rules implemented:
1. Uptrend (ChoCH/BOS up): after IDM, all pullback swing lows left of IDM → demand zones
2. Downtrend (ChoCH/BOS down): after IDM, all pullback swing highs left of IDM → supply zones
3. Clear zones on ChoCH or BOS
4. On IS, draw zones left of IS
5. Demand zone = pullback low → previous high (Rule 6)
6. Supply zone = pullback high → previous low (Rule 7)
7. Show only active (non-mitigated, non-invalidated) zones
"""

import pandas as pd
import numpy as np


def extract_demand_zones(df, cycle_start_idx, search_start_idx, proper_high_idx, active_pb_low_idx):
    """
    Extract demand zones from pullback swing lows in an uptrend leg.
    
    Rule 5/6: In uptrend, lows are pullbacks. Zone = pullback low to previous high.
    Rule 1: Zones occur only left of inducement.
    """
    leg_df = df.loc[cycle_start_idx:proper_high_idx]
    search_df = df.loc[search_start_idx:proper_high_idx]
    sl_rows = search_df[search_df['is_swing_low'] == True]
    # Only include swing lows that are LEFT of the inducement point
    sl_rows = sl_rows[sl_rows.index < active_pb_low_idx]
    
    zones = []
    for z_idx, row in sl_rows.iterrows():
        zone_bottom = float(row['low'])
        
        # Rule 5: zone top = previous swing high peak before this swing low
        prev_df = leg_df.loc[:z_idx]
        prev_df = prev_df.iloc[:-1] if len(prev_df) > 0 else prev_df
        prev_sh = prev_df[prev_df['is_swing_high'] == True]
        if len(prev_sh) > 0:
            zone_top = float(prev_sh['high'].iloc[-1])
        else:
            zone_top = float(prev_df['high'].max()) if len(prev_df) > 0 else float(row['high'])
        
        zones.append({
            'start_time': z_idx,
            'bottom': zone_bottom,
            'top': zone_top,
            'peak': zone_bottom,
            'type': 'demand'
        })
    
    return zones


def extract_supply_zones(df, cycle_start_idx, search_start_idx, proper_low_idx, active_pb_high_idx):
    """
    Extract supply zones from pullback swing highs in a downtrend leg.
    
    Rule 6/7: In downtrend, highs are pullbacks. Zone = pullback high to previous low.
    Rule 2: Zones occur only left of inducement.
    """
    leg_df = df.loc[cycle_start_idx:proper_low_idx]
    search_df = df.loc[search_start_idx:proper_low_idx]
    sh_rows = search_df[search_df['is_swing_high'] == True]
    # Only include swing highs that are LEFT of the inducement point
    sh_rows = sh_rows[sh_rows.index < active_pb_high_idx]
    
    zones = []
    for z_idx, row in sh_rows.iterrows():
        zone_top = float(row['high'])
        
        # Rule 6: zone bottom = previous swing low trough before this swing high
        prev_df = leg_df.loc[:z_idx]
        prev_df = prev_df.iloc[:-1] if len(prev_df) > 0 else prev_df
        prev_sl = prev_df[prev_df['is_swing_low'] == True]
        if len(prev_sl) > 0:
            zone_bottom = float(prev_sl['low'].iloc[-1])
        else:
            zone_bottom = float(prev_df['low'].min()) if len(prev_df) > 0 else float(row['low'])
        
        zones.append({
            'start_time': z_idx,
            'bottom': zone_bottom,
            'top': zone_top,
            'peak': zone_top,
            'type': 'supply'
        })
    
    return zones


class ZoneManager:
    """
    Manages active Supply & Demand zones throughout structure analysis.
    
    Lifecycle:
    - Zones are created on IDM or IS events
    - Zones are mitigated bar-by-bar (price touches zone)
    - Zones are invalidated on BOS or ChoCH (Rule 3)
    - Only active zones are returned (Rule 7)
    """
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.active_demand_zones = []
        self.active_supply_zones = []

    def process_candle(self, idx, c_low, c_high):
        """Mitigate zones bar-by-bar. If price fully penetrates a zone, remove it."""
        if not self.enabled:
            return
        # Demand: mitigated if low <= zone bottom
        for z in self.active_demand_zones[:]:
            if idx > z['start_time'] and c_low <= z['bottom']:
                self.active_demand_zones.remove(z)
        
        # Supply: mitigated if high >= zone top
        for z in self.active_supply_zones[:]:
            if idx > z['start_time'] and c_high >= z['top']:
                self.active_supply_zones.remove(z)

    def handle_idm_uptrend(self, df, choch_idx, proper_high_idx, active_pb_low_idx):
        """Rule 1: On IDM in uptrend, extract demand zones from pullbacks left of IDM."""
        if not self.enabled:
            return
        new_zones = extract_demand_zones(df, choch_idx, choch_idx, proper_high_idx, active_pb_low_idx)
        self.active_demand_zones.extend(new_zones)

    def handle_is_uptrend(self, df, choch_idx, old_proper_high_idx, proper_high_idx, current_pb_low_idx):
        """Rule 4: On IS in uptrend, extract demand zones from pullbacks left of IS."""
        if not self.enabled:
            return
        new_zones = extract_demand_zones(df, choch_idx, old_proper_high_idx, proper_high_idx, current_pb_low_idx)
        self.active_demand_zones.extend(new_zones)

    def handle_idm_downtrend(self, df, choch_idx, proper_low_idx, active_pb_high_idx):
        """Rule 2: On IDM in downtrend, extract supply zones from pullbacks left of IDM."""
        if not self.enabled:
            return
        new_zones = extract_supply_zones(df, choch_idx, choch_idx, proper_low_idx, active_pb_high_idx)
        self.active_supply_zones.extend(new_zones)

    def handle_is_downtrend(self, df, choch_idx, old_proper_low_idx, proper_low_idx, current_pb_high_idx):
        """Rule 4: On IS in downtrend, extract supply zones from pullbacks left of IS."""
        if not self.enabled:
            return
        new_zones = extract_supply_zones(df, choch_idx, old_proper_low_idx, proper_low_idx, current_pb_high_idx)
        self.active_supply_zones.extend(new_zones)

    def clear_on_bos(self, idx):
        """Rule 3: Clear all active zones on BOS."""
        self.active_demand_zones.clear()
        self.active_supply_zones.clear()

    def clear_on_choch(self, idx):
        """Rule 3: Clear all active zones on ChoCH."""
        self.active_demand_zones.clear()
        self.active_supply_zones.clear()

    def finalize(self, last_idx):
        """Set end_time on remaining active zones at dataset end."""
        for z in self.active_demand_zones:
            z['end_time'] = last_idx
            z['end_time'] = last_idx

    def get_all_zones(self):
        """Rule 7: Return only currently active zones."""
        all_active = []
        for z in self.active_demand_zones:
            zone_copy = dict(z)
            zone_copy['status'] = 'active'
            all_active.append(zone_copy)
        for z in self.active_supply_zones:
            zone_copy = dict(z)
            zone_copy['status'] = 'active'
            all_active.append(zone_copy)
        return all_active
