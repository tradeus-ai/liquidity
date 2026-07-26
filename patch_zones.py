with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/smc_zones.py', 'r') as f:
    code = f.read()

# Add a function to dynamically add/merge a zone
add_zone_func = """
def add_zone(active_zones, start_time, bottom, top, peak, zone_type, threshold=0.003):
    # Try to merge with an existing zone
    for z in active_zones:
        # Both must be the same type, but they are since lists are separated
        diff = abs(z['peak'] - peak) / z['peak']
        if diff <= threshold:
            z['bottom'] = min(z['bottom'], bottom)
            z['top'] = max(z['top'], top)
            z['start_time'] = start_time
            # Update history with the new bounds
            z['history'].append({'time': start_time, 'top': z['top'], 'bottom': z['bottom']})
            return
            
    # Not merged, add as new
    active_zones.append({
        'start_time': start_time,
        'bottom': bottom,
        'top': top,
        'peak': peak,
        'type': zone_type,
        'history': [{'time': start_time, 'top': top, 'bottom': bottom}]
    })

"""

code = add_zone_func + code

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/smc_zones.py', 'w') as f:
    f.write(code)

