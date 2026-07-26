with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/structure_service.py', 'r') as f:
    code = f.read()

# Replace the htf_events iteration
old_logic = """    if tf == '1d':
        # Analyze Higher Timeframe Market Structure (BOS, ChoCH, Inducement)
        raw_events = analyze_htf_structure(df_struct)
        for ev in raw_events:
            st_ts = int(pd.to_datetime(ev['start_time']).timestamp())
            et_ts = int(pd.to_datetime(ev['end_time']).timestamp())
            htf_events.append({
                'type': ev['type'],
                'label': ev['label'],
                'start_time': st_ts,
                'start_val': float(ev['start_val']),
                'end_time': et_ts,
                'end_val': float(ev['end_val']),
                'color': ev['color']
            })

        zones_df = df_struct.dropna(subset=['zone_type'])"""

new_logic = """    htf_zones = []
    if tf == '1d':
        # Analyze Higher Timeframe Market Structure (BOS, ChoCH, Inducement)
        res = analyze_htf_structure(df_struct)
        raw_events = res['events']
        raw_zones = res['zones']
        
        for ev in raw_events:
            st_ts = int(pd.to_datetime(ev['start_time']).timestamp())
            et_ts = int(pd.to_datetime(ev['end_time']).timestamp())
            htf_events.append({
                'type': ev['type'],
                'label': ev['label'],
                'start_time': st_ts,
                'start_val': float(ev['start_val']),
                'end_time': et_ts,
                'end_val': float(ev['end_val']),
                'color': ev['color']
            })
            
        for z in raw_zones:
            st_ts = int(pd.to_datetime(z['start_time']).timestamp())
            et_ts = int(pd.to_datetime(z['end_time']).timestamp()) if z.get('end_time') else None
            
            history = []
            for h in z.get('history', []):
                h_ts = int(pd.to_datetime(h['time']).timestamp())
                history.append({'time': h_ts, 'top': h['top'], 'bottom': h['bottom']})
                
            htf_zones.append({
                'type': z['type'],
                'start_time': st_ts,
                'end_time': et_ts,
                'bottom': z['bottom'],
                'top': z['top'],
                'peak': z['peak'],
                'status': z['status'],
                'history': history
            })

        zones_df = df_struct.dropna(subset=['zone_type'])"""
        
code = code.replace(old_logic, new_logic)

# Replace payload assignment
payload_old = """    payload = {
        'symbol': symbol_raw,
        'timeframe': tf,
        'is_intraday': is_intraday,
        'candles': candles,
        'pullback_points': pullback_points,
        'inside_zones': inside_zones,
        'zones': zones,
        'htf_events': htf_events
    }"""
    
payload_new = """    payload = {
        'symbol': symbol_raw,
        'timeframe': tf,
        'is_intraday': is_intraday,
        'candles': candles,
        'pullback_points': pullback_points,
        'inside_zones': inside_zones,
        'zones': zones,
        'htf_events': htf_events,
        'htf_zones': htf_zones
    }"""

code = code.replace(payload_old, payload_new)

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/structure_service.py', 'w') as f:
    f.write(code)

