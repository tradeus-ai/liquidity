import os
import pandas as pd
from symbol_loader import get_symbol_list
from structure_service import get_chart_data
from lightweight_charts.widgets import StaticLWC

def render_dashboard(symbol_raw="AMBUJACEM", timeframe_raw="1d"):
    tf = timeframe_raw.lower()
    data = get_chart_data(symbol_raw, tf)
    
    if 'error' in data:
        return f"<h1>Error: {data['error']}</h1>"
        
    is_intraday = data.get('is_intraday', False)
    
    # Create StaticLWC chart
    chart = StaticLWC(toolbox=True)
    chart.layout(background_color='#131722', text_color='#d1d4dc')
    chart.candle_style(
        up_color='#ffffff',
        down_color='#ffffff',
        border_up_color='#ffffff',
        border_down_color='#ffffff',
        wick_up_color='#ffffff',
        wick_down_color='#ffffff'
    )
    chart.time_scale(time_visible=is_intraday, seconds_visible=False)
    chart.legend(visible=True, ohlc=True, percent=True, font_size=20)
    
    # Format candle dataframe for lightweight-charts
    candles_df = pd.DataFrame(data['candles'])
    candles_df['time'] = pd.to_datetime(candles_df['time'], unit='s').astype('datetime64[ns]')
    chart.set(candles_df[['time', 'open', 'high', 'low', 'close']])
    
    # Add pullback line
    if len(data.get('pullback_points', [])) > 1:
        line_df = pd.DataFrame(data['pullback_points'])
        line_df['time'] = pd.to_datetime(line_df['time'], unit='s').astype('datetime64[ns]')
        line = chart.create_line(color='#ff9800', width=3)
        line.set(line_df)
        
    # HTF Structure Events (#, IS, BOS, ChoCH) - ONLY for Daily - 1D
    if tf == '1d':
        for ev in data.get('htf_events', []):
            st_date = pd.to_datetime(ev['start_time'], unit='s').strftime('%Y-%m-%d')
            et_date = pd.to_datetime(ev['end_time'], unit='s').strftime('%Y-%m-%d')
            chart.trend_line(
                start_time=st_date, start_value=ev['start_val'],
                end_time=et_date, end_value=ev['end_val'],
                line_color=ev['color'], width=2, style='solid'
            )

    # Demand/Supply zones (ONLY for Daily - 1D)
    for z in data.get('zones', []):
        st_date = pd.to_datetime(z['start_time'], unit='s').strftime('%Y-%m-%d')
        et_date = pd.to_datetime(z['end_time'], unit='s').strftime('%Y-%m-%d')
        color = 'rgba(0, 255, 0, 0.2)' if z['type'] == 'DEMAND' else 'rgba(255, 0, 0, 0.2)'
        line_color = 'green' if z['type'] == 'DEMAND' else 'red'
        chart.box(
            start_time=st_date, start_value=z['high'],
            end_time=et_date, end_value=z['low'],
            color=line_color, fill_color=color, width=1
        )
        
    # Inside bar zones (pink rectangle)
    time_fmt = '%Y-%m-%d %H:%M:%S' if is_intraday else '%Y-%m-%d'
    for z in data.get('inside_zones', []):
        st_date = pd.to_datetime(z['start_time'], unit='s').strftime(time_fmt)
        et_date = pd.to_datetime(z['end_time'], unit='s').strftime(time_fmt)
        chart.box(
            start_time=st_date, start_value=z['high'],
            end_time=et_date, end_value=z['low'],
            color='pink', fill_color='rgba(255, 105, 180, 0.2)', width=1
        )
        
    chart.load()
    
    # Symbols dropdown options
    symbols = get_symbol_list()
    symbol_options = "".join(f'<option value="{s}" {"selected" if s == symbol_raw else ""}>{s}</option>' for s in symbols)
    
    topbar_ui = f"""
    <style>
    html, body {{
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        background-color: #131722;
    }}
    body {{
        padding-top: 50px !important;
    }}
    
    .legend {{ font-size: 20px !important; font-weight: 600 !important; }}
    
    .custom-topbar {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        width: 100%;
        height: 50px;
        background-color: #1e222d;
        border-bottom: 1px solid #363c4e;
        display: flex;
        align-items: center;
        padding: 0 15px;
        gap: 15px;
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        box-sizing: border-box;
    }}
    .custom-topbar .title {{
        color: #fff;
        font-weight: 600;
        font-size: 15px;
        margin-right: 10px;
    }}
    .custom-topbar select {{
        background: #131722;
        color: #fff;
        border: 1px solid #363c4e;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 14px;
        outline: none;
        cursor: pointer;
    }}
    .custom-topbar .tf-group {{
        display: flex;
        gap: 4px;
        background: #131722;
        padding: 3px;
        border-radius: 4px;
        border: 1px solid #363c4e;
    }}
    .custom-topbar .tf-btn {{
        background: transparent;
        color: #848e9c;
        border: none;
        padding: 4px 10px;
        border-radius: 3px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
    }}
    .custom-topbar .tf-btn:hover {{
        color: #fff;
    }}
    .custom-topbar .tf-btn.active {{
        background: #2962ff;
        color: #fff;
    }}
    .handler, #container {{
        height: calc(100vh - 50px) !important;
    }}
    </style>

    <div class="custom-topbar">
        <div class="title">📊 Liquidity Finder</div>
        <div>
            <label style="font-size:12px; color:#848e9c; margin-right:5px;">Symbol:</label>
            <select id="top-symbol-select" onchange="changeSymbol(this.value)">
                {symbol_options}
            </select>
        </div>
        <div class="tf-group">
            <button class="tf-btn {'active' if tf=='1d' else ''}" onclick="changeTF('1d')">1D</button>
            <button class="tf-btn {'active' if tf=='1h' else ''}" onclick="changeTF('1h')">1H</button>
            <button class="tf-btn {'active' if tf=='15m' else ''}" onclick="changeTF('15m')">15m</button>
            <button class="tf-btn {'active' if tf=='5m' else ''}" onclick="changeTF('5m')">5m</button>
        </div>
        <div style="display:flex; gap:10px; align-items:center; margin-left:10px;">
            <label style="cursor:pointer; color:#00e676; font-weight:700; font-size:12px; background:#131722; padding:3px 6px; border-radius:4px; border:1px solid #363c4e;">
                <input type="checkbox" id="toggle-master" checked onchange="toggleMaster(this.checked)"> Master SMC Structure
            </label>
            <span style="color:#363c4e;">|</span>
            <label style="cursor:pointer; color:#ff9800; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-pullbacks" checked onchange="toggleLayers()"> Pullbacks</label>
            <label style="cursor:pointer; color:#ffb300; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-idm" checked onchange="toggleLayers()"> # (IDM)</label>
            <label style="cursor:pointer; color:#00e5ff; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-is" checked onchange="toggleLayers()"> IS</label>
            <label style="cursor:pointer; color:#2962ff; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-bos" checked onchange="toggleLayers()"> BOS</label>
            <label style="cursor:pointer; color:#e91e63; font-size:12px;"><input type="checkbox" class="layer-toggle" id="toggle-choch" checked onchange="toggleLayers()"> ChoCH</label>
        </div>
    </div>

    <div id="feedback-panel" style="position:fixed; bottom:20px; right:20px; z-index:10000; background:#1e222d; color:#d1d4dc; padding:15px; border-radius:8px; border: 1px solid #434651; box-shadow: 0 4px 6px rgba(0,0,0,0.3); font-family: sans-serif; width: 300px;">
       <h3 style="margin-top:0; color:#fff;">Correction Feedback</h3>
       <p style="font-size:12px; margin-bottom:10px;">Use the toolbox to draw lines/boxes, then describe the mistake below to send to the AI.</p>
       <textarea id="feedback-text" rows="3" style="width:100%; background:#131722; color:#fff; border:1px solid #434651; border-radius:4px; padding:5px; margin-bottom:5px;" placeholder="E.g., Missing swing low at 2026-07-21 14:15..."></textarea>
       <button onclick="sendFeedback()" style="width:100%; background:#2962ff; color:#fff; border:none; padding:8px; border-radius:4px; cursor:pointer; font-weight:bold;">Send Feedback</button>
    </div>

    <script>
    window.addEventListener('DOMContentLoaded', function() {{
        setTimeout(function() {{
            try {{
                for (let key in window) {{
                    if (key.startsWith('chart_') && window[key].chart) {{
                        const handler = window[key];
                        const legendText = handler.legend.text;
                        legendText.style.marginRight = "15px";
                        legendText.style.fontWeight = "bold";
                        legendText.style.color = "#2962ff";
                        
                        handler.chart.subscribeCrosshairMove(function(param) {{
                            if (param && param.time) {{
                                let dateStr = "";
                                if (typeof param.time === 'number') {{
                                    const d = new Date(param.time * 1000);
                                    const y = d.getUTCFullYear();
                                    const m = String(d.getUTCMonth() + 1).padStart(2, '0');
                                    const day = String(d.getUTCDate()).padStart(2, '0');
                                    const hh = String(d.getUTCHours()).padStart(2, '0');
                                    const mm = String(d.getUTCMinutes()).padStart(2, '0');
                                    if ('{tf}' === '1d') {{
                                        dateStr = `${{y}}-${{m}}-${{day}}`;
                                    }} else {{
                                        dateStr = `${{y}}-${{m}}-${{day}} ${{hh}}:${{mm}}`;
                                    }}
                                }} else if (typeof param.time === 'object') {{
                                    const y = param.time.year;
                                    const m = String(param.time.month).padStart(2, '0');
                                    const day = String(param.time.day).padStart(2, '0');
                                    dateStr = `${{y}}-${{m}}-${{day}}`;
                                }} else {{
                                    dateStr = String(param.time);
                                }}
                                legendText.innerText = dateStr;
                            }} else {{
                                legendText.innerText = "";
                            }}
                        }});
                    }}
                }}
            }} catch(e) {{
                console.error("Error attaching legend date listener:", e);
            }}
        }}, 500);
    }});

    function changeSymbol(sym) {{
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('symbol', sym);
        window.location.search = urlParams.toString();
    }}
    function changeTF(tf) {{
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('timeframe', tf);
        window.location.search = urlParams.toString();
    }}
    function sendFeedback() {{
        const text = document.getElementById('feedback-text').value;
        const btn = document.querySelector('button[onclick="sendFeedback()"]');
        const urlParams = new URLSearchParams(window.location.search);
        const currentSym = urlParams.get('symbol') || '{symbol_raw}';
        const currentTF = urlParams.get('timeframe') || '{tf}';

        let drawings = null;
        try {{
            for (let i = 0; i < localStorage.length; i++) {{
                let key = localStorage.key(i);
                if (key.includes('drawings')) {{
                    drawings = JSON.parse(localStorage.getItem(key));
                }}
            }}
        }} catch(e) {{}}

        const payload = {{
            symbol: currentSym,
            timeframe: currentTF,
            timestamp: new Date().toISOString(),
            description: text,
            drawings: drawings
        }};

        btn.innerText = "Sending...";
        fetch('/api/feedback', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(payload)
        }}).then(res => {{
            if(res.ok) {{
                btn.innerText = "✅ Sent!";
                btn.style.background = "#089981";
                setTimeout(() => {{ btn.innerText = "Send Feedback"; btn.style.background = "#2962ff"; }}, 2000);
            }} else {{
                alert("Error saving feedback.");
                btn.innerText = "Send Feedback";
            }}
        }}).catch(err => {{
            alert("Connection failed!");
            btn.innerText = "Send Feedback";
        }});
    }}
    </script>
    """
    
    full_html = f"{chart._html}</script>{topbar_ui}</body></html>"
    return full_html
