import re

# PATCH main.py
with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/main.py', 'r') as f:
    code = f.read()
code = code.replace("htf_events = analyze_htf_structure(df)", """res = analyze_htf_structure(df)
        htf_events = res['events']
        htf_zones = res['zones']""")
with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/main.py', 'w') as f:
    f.write(code)

# PATCH app.py
with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/app.py', 'r') as f:
    code = f.read()
code = code.replace("htf_events = analyze_htf_structure(df)", """res = analyze_htf_structure(df)
        htf_events = res['events']
        htf_zones = res['zones']""")
code = code.replace("'htf_events': htf_events,", "'htf_events': htf_events,\n            'htf_zones': htf_zones,")
# Note: we need to handle the time conversion for htf_zones in app.py
app_json_patch = """
        # Convert events times
        for ev in htf_events:
            ev['start_time'] = int(pd.Timestamp(ev['start_time']).timestamp())
            ev['end_time'] = int(pd.Timestamp(ev['end_time']).timestamp())
            
        for z in htf_zones:
            z['start_time'] = int(pd.Timestamp(z['start_time']).timestamp())
            if z['end_time']:
                z['end_time'] = int(pd.Timestamp(z['end_time']).timestamp())
            for h in z['history']:
                h['time'] = int(pd.Timestamp(h['time']).timestamp())
"""
code = code.replace("""        for ev in htf_events:
            ev['start_time'] = int(pd.Timestamp(ev['start_time']).timestamp())
            ev['end_time'] = int(pd.Timestamp(ev['end_time']).timestamp())""", app_json_patch)
with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/app.py', 'w') as f:
    f.write(code)

