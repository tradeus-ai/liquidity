import re

# 1. Update bos_choch_inducement.py to invalidate zones on BOS / ChoCH
with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'r') as f:
    code = f.read()

def inject_invalidation(code, trigger_line, invalidation_label):
    injection = f"""{trigger_line}
                            # Invalidate old zones
                            for z in active_demand_zones:
                                z['end_time'] = idx
                                z['status'] = '{invalidation_label}'
                                historical_zones.append(z)
                            active_demand_zones.clear()
                            
                            for z in active_supply_zones:
                                z['end_time'] = idx
                                z['status'] = '{invalidation_label}'
                                historical_zones.append(z)
                            active_supply_zones.clear()"""
    return code.replace(trigger_line, injection)

# ChoCH Uptrend
code = inject_invalidation(code, "current_trend = 1", "invalidated_by_choch")
# BOS Uptrend
code = inject_invalidation(code, "inducement_done = False", "invalidated_by_bos")
# ChoCH Downtrend
code = inject_invalidation(code, "current_trend = -1", "invalidated_by_choch")

# The BOS replacement injected it twice because inducement_done = False appears twice.
# That's exactly correct (once for uptrend BOS, once for downtrend BOS).

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/bos_choch_inducement.py', 'w') as f:
    f.write(code)

# 2. Update dashboard.html
with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/dashboard.html', 'r') as f:
    html = f.read()

# Fix CSS for time scale
html = html.replace("""        header {
            height: 55px;""", """        header {
            height: 55px;
            flex-shrink: 0;""")
html = html.replace("""        #chart-container {
            flex: 1;
            width: 100%;
            position: relative;
        }""", """        #chart-container {
            flex: 1;
            width: 100%;
            position: relative;
            min-height: 0;
        }""")

# Remove checkboxes
checkboxes_to_remove = """            <label style="cursor:pointer; color:#00e676; font-weight:700; font-size:13px; background:#131722; padding:4px 8px; border-radius:4px; border:1px solid #363c4e;">
                <input type="checkbox" id="toggle-master" checked onchange="toggleMaster(this.checked)"> Master SMC Structure
            </label>
            <span style="color:#363c4e;">|</span>
            <label style="cursor:pointer; color:#ff9800; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-pullbacks" checked onchange="toggleLayers()"> Pullbacks</label>
            <label style="cursor:pointer; color:#ffb300; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-idm" checked onchange="toggleLayers()"> # (IDM)</label>
            <label style="cursor:pointer; color:#00e5ff; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-is" checked onchange="toggleLayers()"> IS</label>
            <label style="cursor:pointer; color:#2962ff; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-bos" checked onchange="toggleLayers()"> BOS</label>
            <label style="cursor:pointer; color:#e91e63; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-choch" checked onchange="toggleLayers()"> ChoCH</label>
            <span style="color:#363c4e;">|</span>"""
            
html = html.replace(checkboxes_to_remove, """            <label style="cursor:pointer; color:#ff9800; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-pullbacks" checked onchange="toggleLayers()"> Pullbacks</label>
            <span style="color:#363c4e;">|</span>""")

# Change 1H to 1W
html = html.replace('<button class="tf-btn" data-tf="1h">1H</button>', '<button class="tf-btn" data-tf="1w">1W</button>')

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/dashboard.html', 'w') as f:
    f.write(html)

# 3. Update structure_service.py for 1W timeframe
with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/structure_service.py', 'r') as f:
    ss = f.read()

ss = ss.replace("'1d': (Interval.in_daily, '1d'),", "'1w': (Interval.in_weekly, '1W'),\n    '1d': (Interval.in_daily, '1d'),")
ss = ss.replace("'1d': '15m',", "'1w': '1d',\n    '1d': '15m',")

with open('/mnt/all/Trading/Courses/Xoduse/Liquidity/structure_service.py', 'w') as f:
    f.write(ss)

