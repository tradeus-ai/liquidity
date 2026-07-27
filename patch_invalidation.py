with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'r') as f:
    code = f.read()

# 1. Uptrend ChoCH
choch_up = """                        # CHOCH happened (Trend Reversed to UPTREND)
                        current_trend = 1"""
choch_up_new = choch_up + """
                        for z in active_demand_zones:
                            z['end_time'] = idx
                            z['status'] = 'invalidated_by_choch'
                            historical_zones.append(z)
                        active_demand_zones.clear()
                        for z in active_supply_zones:
                            z['end_time'] = idx
                            z['status'] = 'invalidated_by_choch'
                            historical_zones.append(z)
                        active_supply_zones.clear()"""
code = code.replace(choch_up, choch_up_new)

# 2. Downtrend ChoCH
choch_down = """                        # CHOCH happened (Trend Reversed to DOWNTREND)
                        current_trend = -1"""
choch_down_new = choch_down + """
                        for z in active_demand_zones:
                            z['end_time'] = idx
                            z['status'] = 'invalidated_by_choch'
                            historical_zones.append(z)
                        active_demand_zones.clear()
                        for z in active_supply_zones:
                            z['end_time'] = idx
                            z['status'] = 'invalidated_by_choch'
                            historical_zones.append(z)
                        active_supply_zones.clear()"""
code = code.replace(choch_down, choch_down_new)

# 3. Uptrend BOS
bos_up = """                        if c_close > target_high:
                            structure_events.append({
                                'type': 'BOS',
                                'label': 'BOS',
                                'start_time': proper_high_idx,
                                'start_val': proper_high_val,
                                'end_time': idx,
                                'end_val': proper_high_val,
                                'color': '#2962ff'
                            })"""
bos_up_new = bos_up + """
                            for z in active_demand_zones:
                                z['end_time'] = idx
                                z['status'] = 'invalidated_by_bos'
                                historical_zones.append(z)
                            active_demand_zones.clear()
                            for z in active_supply_zones:
                                z['end_time'] = idx
                                z['status'] = 'invalidated_by_bos'
                                historical_zones.append(z)
                            active_supply_zones.clear()"""
code = code.replace(bos_up, bos_up_new)

# 4. Downtrend BOS
bos_down = """                        if c_close < target_low:
                            structure_events.append({
                                'type': 'BOS',
                                'label': 'BOS',
                                'start_time': proper_low_idx,
                                'start_val': proper_low_val,
                                'end_time': idx,
                                'end_val': proper_low_val,
                                'color': '#2962ff'
                            })"""
bos_down_new = bos_down + """
                            for z in active_demand_zones:
                                z['end_time'] = idx
                                z['status'] = 'invalidated_by_bos'
                                historical_zones.append(z)
                            active_demand_zones.clear()
                            for z in active_supply_zones:
                                z['end_time'] = idx
                                z['status'] = 'invalidated_by_bos'
                                historical_zones.append(z)
                            active_supply_zones.clear()"""
code = code.replace(bos_down, bos_down_new)

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'w') as f:
    f.write(code)

