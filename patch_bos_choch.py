import re

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'r') as f:
    code = f.read()

# 1. Add merge_zones function
merge_func = """
def merge_zones(raw_zones, threshold=0.003):
    if not raw_zones: return []
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

def analyze_htf_structure(df):
"""
code = code.replace("def analyze_htf_structure(df):", merge_func)

# 2. Add zone arrays
zone_init = """
    structure_events = []
    active_demand_zones = []
    active_supply_zones = []
    historical_zones = []
"""
code = code.replace("    structure_events = []", zone_init)

# 3. Trigger zones on Inducement (UPTREND)
uptrend_idm_orig = """                            structure_events.append({
                                'type': evt_type,
                                'label': label,
                                'start_time': active_pb_low_idx,
                                'start_val': active_pb_low_val,
                                'end_time': idx,
                                'end_val': active_pb_low_val,
                                'color': '#00e5ff' if evt_type == 'IS' else '#ffd600'
                            })"""
uptrend_idm_new = uptrend_idm_orig + """
                            
                            # Uptrend Confirmed: Identify Demand Zones
                            if evt_type == 'IDM':
                                leg_df = df.loc[cycle_start_idx:proper_high_idx]
                                sl_rows = leg_df[leg_df['is_swing_low'] == True]
                                sl_rows = sl_rows[sl_rows.index < active_pb_low_idx]
                                raw_zones = []
                                for z_idx, row in sl_rows.iterrows():
                                    raw_zones.append({
                                        'start_time': z_idx,
                                        'bottom': float(row['low']),
                                        'top': float(row['high']),
                                        'peak': float(row['low']),
                                        'type': 'demand'
                                    })
                                merged_zones = merge_zones(raw_zones, threshold=0.003)
                                active_demand_zones.extend(merged_zones)
"""
code = code.replace(uptrend_idm_orig, uptrend_idm_new)

# 4. Trigger zones on Inducement (DOWNTREND)
downtrend_idm_orig = """                            structure_events.append({
                                'type': evt_type,
                                'label': label,
                                'start_time': active_pb_high_idx,
                                'start_val': active_pb_high_val,
                                'end_time': idx,
                                'end_val': active_pb_high_val,
                                'color': '#00e5ff' if evt_type == 'IS' else '#ffd600'
                            })"""
downtrend_idm_new = downtrend_idm_orig + """
                            
                            # Downtrend Confirmed: Identify Supply Zones
                            if evt_type == 'IDM':
                                leg_df = df.loc[cycle_start_idx:proper_low_idx]
                                sh_rows = leg_df[leg_df['is_swing_high'] == True]
                                sh_rows = sh_rows[sh_rows.index < active_pb_high_idx]
                                raw_zones = []
                                for z_idx, row in sh_rows.iterrows():
                                    raw_zones.append({
                                        'start_time': z_idx,
                                        'bottom': float(row['low']),
                                        'top': float(row['high']),
                                        'peak': float(row['high']),
                                        'type': 'supply'
                                    })
                                merged_zones = merge_zones(raw_zones, threshold=0.003)
                                active_supply_zones.extend(merged_zones)
"""
code = code.replace(downtrend_idm_orig, downtrend_idm_new)

# 5. Zone Mitigation Logic at the end of the main loop
mitigation_logic = """
            if current_trend == prev_trend:
                break
            trends_processed += 1
            
        # --- Mitigate Active Zones with the current candle ---
        # Demand Zones (touched if low dips into top)
        for z in active_demand_zones[:]:
            if c_low < z['top']:
                if c_low <= z['bottom']:
                    z['end_time'] = idx
                    z['status'] = 'mitigated'
                    historical_zones.append(z)
                    active_demand_zones.remove(z)
                else:
                    z['top'] = c_low
                    z['history'].append({'time': idx, 'top': z['top'], 'bottom': z['bottom']})
                    
        # Supply Zones (touched if high pierces bottom)
        for z in active_supply_zones[:]:
            if c_high > z['bottom']:
                if c_high >= z['top']:
                    z['end_time'] = idx
                    z['status'] = 'mitigated'
                    historical_zones.append(z)
                    active_supply_zones.remove(z)
                else:
                    z['bottom'] = c_high
                    z['history'].append({'time': idx, 'top': z['top'], 'bottom': z['bottom']})

    # Finalize remaining active zones
    for z in active_demand_zones:
        z['end_time'] = df.index[-1]
        z['status'] = 'active'
        historical_zones.append(z)
        
    for z in active_supply_zones:
        z['end_time'] = df.index[-1]
        z['status'] = 'active'
        historical_zones.append(z)

    return {
        'events': structure_events,
        'zones': historical_zones
    }
"""
code = code.replace("""
            if current_trend == prev_trend:
                break
            trends_processed += 1

    return structure_events""", mitigation_logic)

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'w') as f:
    f.write(code)

