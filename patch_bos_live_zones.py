import re

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'r') as f:
    code = f.read()

# 1. Update import
code = code.replace("from smc_zones import extract_demand_zones, extract_supply_zones, mitigate_zones, finalize_zones",
                    "from smc_zones import extract_demand_zones, extract_supply_zones, mitigate_zones, finalize_zones, add_zone")

# 2. Add logic to uptrend (if inducement_done == True and is_sl == True, add demand zone)
uptrend_else = """                    else:
                        target_high = wick_high_val if wick_high_val is not None else proper_high_val"""

uptrend_else_new = """                    else:
                        # Once trend is confirmed by IDM, every new valid swing low is a Demand Zone
                        if is_sl:
                            add_zone(active_demand_zones, idx, c_low, c_high, c_low, 'demand', 0.003)

                        target_high = wick_high_val if wick_high_val is not None else proper_high_val"""
code = code.replace(uptrend_else, uptrend_else_new)

# 3. Add logic to downtrend (if inducement_done == True and is_sh == True, add supply zone)
downtrend_else = """                    else:
                        target_low = wick_low_val if wick_low_val is not None else proper_low_val"""

downtrend_else_new = """                    else:
                        # Once trend is confirmed by IDM, every new valid swing high is a Supply Zone
                        if is_sh:
                            add_zone(active_supply_zones, idx, c_low, c_high, c_high, 'supply', 0.003)

                        target_low = wick_low_val if wick_low_val is not None else proper_low_val"""
code = code.replace(downtrend_else, downtrend_else_new)

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'w') as f:
    f.write(code)

