import re

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'r') as f:
    code = f.read()

# 1. Import at the top
if 'from smc_zones import' not in code:
    code = code.replace('import numpy as np', 'import numpy as np\nfrom smc_zones import extract_demand_zones, extract_supply_zones, mitigate_zones, finalize_zones')

# 2. Remove merge_zones
code = re.sub(r'def merge_zones.*?return merged\n', '', code, flags=re.DOTALL)

# 3. Replace Demand zone logic
demand_logic_old = """                            # Uptrend Confirmed: Identify Demand Zones
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
                                active_demand_zones.extend(merged_zones)"""
demand_logic_new = """                            # Uptrend Confirmed: Identify Demand Zones
                            if evt_type == 'IDM':
                                merged_zones = extract_demand_zones(df, cycle_start_idx, proper_high_idx, active_pb_low_idx, 0.003)
                                active_demand_zones.extend(merged_zones)"""
code = code.replace(demand_logic_old, demand_logic_new)

# 4. Replace Supply zone logic
supply_logic_old = """                            # Downtrend Confirmed: Identify Supply Zones
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
                                active_supply_zones.extend(merged_zones)"""
supply_logic_new = """                            # Downtrend Confirmed: Identify Supply Zones
                            if evt_type == 'IDM':
                                merged_zones = extract_supply_zones(df, cycle_start_idx, proper_low_idx, active_pb_high_idx, 0.003)
                                active_supply_zones.extend(merged_zones)"""
code = code.replace(supply_logic_old, supply_logic_new)

# 5. Replace mitigation and finalize logic
mitigate_logic_old = """        # --- Mitigate Active Zones with the current candle ---
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
        historical_zones.append(z)"""

mitigate_logic_new = """        # --- Mitigate Active Zones with the current candle ---
        mitigate_zones(active_demand_zones, active_supply_zones, historical_zones, c_low, c_high, idx)

    # Finalize remaining active zones
    finalize_zones(active_demand_zones, active_supply_zones, historical_zones, df.index[-1])"""
code = code.replace(mitigate_logic_old, mitigate_logic_new)

# Also fix the weird extra spaces the user left at the top
code = code.replace('\n\n\n    structure_events = []', '\n    structure_events = []')
code = code.replace('def analyze_htf_structure(df):\n\n    """', 'def analyze_htf_structure(df):\n    """')

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'w') as f:
    f.write(code)

