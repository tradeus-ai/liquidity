with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/smc_zones.py', 'r') as f:
    code = f.read()

# Add idx > z['start_time'] check
demand_old = "if c_low < z['top']:"
demand_new = "if idx > z['start_time'] and c_low < z['top']:"
code = code.replace(demand_old, demand_new)

supply_old = "if c_high > z['bottom']:"
supply_new = "if idx > z['start_time'] and c_high > z['bottom']:"
code = code.replace(supply_old, supply_new)

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/smc_zones.py', 'w') as f:
    f.write(code)

