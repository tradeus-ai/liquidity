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

# Test
zones = [
    {'start_time': 1, 'bottom': 99, 'top': 101, 'peak': 100},
    {'start_time': 2, 'bottom': 100, 'top': 102, 'peak': 100.1},
    {'start_time': 3, 'bottom': 105, 'top': 106, 'peak': 105.5}
]
print(merge_zones(zones))
