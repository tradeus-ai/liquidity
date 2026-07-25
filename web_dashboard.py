import os
import pandas as pd
from tvDatafeed import Interval
from data_fetcher import DataFetcher
from market_structure import MarketStructureAnalyzer
from smc_pullback import find_swings
from inside_bars import identify_inside_bar_zones
from symbol_loader import get_symbol_list
from lightweight_charts.widgets import StaticLWC

fetcher = DataFetcher(data_dir="data")

TIMEFRAME_MAP = {
    '1d': (Interval.in_daily, '1d'),
    '1h': (Interval.in_1_hour, '1h'),
    '15m': (Interval.in_15_minute, '15m'),
    '5m': (Interval.in_5_minute, '5m')
}

LTF_MAP = {
    '1d': '15m',
    '1h': '5m',
    '15m': '5m',
    '5m': None
}

def render_dashboard(symbol_raw="AMBUJACEM", timeframe_raw="1d"):
    tf = timeframe_raw.lower()
    if tf not in TIMEFRAME_MAP:
        tf = '1d'
        
    tv_symbol = f"{symbol_raw}1!" if not symbol_raw.endswith('1!') else symbol_raw
    exchange = 'NSE'
    
    interval_enum, interval_name = TIMEFRAME_MAP[tf]
    
    # LTF for outside bar resolution
    ltf_name = LTF_MAP.get(tf)
    ltf_df = None
    if ltf_name and ltf_name in TIMEFRAME_MAP:
        ltf_enum, ltf_str = TIMEFRAME_MAP[ltf_name]
        ltf_df = fetcher.fetch_data(tv_symbol, exchange, ltf_enum, ltf_str, n_bars_initial=2000, n_bars_update=300)
        
    df = fetcher.fetch_data(tv_symbol, exchange, interval_enum, interval_name, n_bars_initial=3000, n_bars_update=500)
    
    if df is None or df.empty:
        return f"<h1>Error: Failed to fetch data for {tv_symbol} ({tf})</h1>"
        
    analyzer = MarketStructureAnalyzer(df, timeframe=tf, ltf_df=ltf_df)
    df_struct = analyzer.identify_structure()
    
    is_intraday = tf in ['1h', '15m', '5m']
    time_format = '%Y-%m-%d %H:%M:%S' if is_intraday else '%Y-%m-%d'
    
    if pd.api.types.is_datetime64_any_dtype(df_struct.index):
        df_struct.index = df_struct.index.strftime(time_format)
        
    df_plot = df_struct.copy()
    if df_plot.index.name != 'time':
        df_plot = df_plot.reset_index()
        df_plot.rename(columns={df_plot.columns[0]: 'time'}, inplace=True)
    df_plot.columns = [c.lower() for c in df_plot.columns]
    
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
    
    df_plot['time'] = pd.to_datetime(df_plot['time']).astype('datetime64[ns]')
    chart.set(df_plot[['time', 'open', 'high', 'low', 'close']])
    
    # Pullback line
    pullback_points = []
    last_swing = None
    for idx, row in df_struct.iterrows():
        is_high = row.get('is_swing_high', False)
        is_low = row.get('is_swing_low', False)
        if is_high and is_low:
            if last_swing == 'HIGH':
                pullback_points.append({'time': idx, 'value': row['low']})
                pullback_points.append({'time': idx, 'value': row['high']})
                last_swing = 'HIGH'
            else:
                pullback_points.append({'time': idx, 'value': row['high']})
                pullback_points.append({'time': idx, 'value': row['low']})
                last_swing = 'LOW'
        elif is_high:
            pullback_points.append({'time': idx, 'value': row['high']})
            last_swing = 'HIGH'
        elif is_low:
            pullback_points.append({'time': idx, 'value': row['low']})
            last_swing = 'LOW'
            
    if len(pullback_points) > 1:
        line_df = pd.DataFrame(pullback_points)
        line_df['time'] = pd.to_datetime(line_df['time']).astype('datetime64[ns]')
        line = chart.create_line(color='#ff9800', width=3)
        line.set(line_df)
        
    # Structure events (BOS, CHOCH) - ONLY for Higher Timeframe Daily (1D)
    if tf == '1d':
        events = df_struct.dropna(subset=['structure_event'])
        min_date = df_struct.index[0]
        for idx, row in events.iterrows():
            if pd.notna(row.get('event_start_idx')):
                start_date = pd.to_datetime(row['event_start_idx']).strftime(time_format)
                end_date = pd.to_datetime(row['event_end_idx']).strftime(time_format)
                start_val = row['event_start_val']
                end_val = row['event_end_val']
                if start_date < min_date:
                    start_date = min_date
                chart.trend_line(
                    start_time=start_date, start_value=start_val,
                    end_time=end_date, end_value=end_val,
                    line_color='blue', width=2, style='dashed'
                )
                
        # Demand/Supply zones - ONLY for Higher Timeframe Daily (1D)
        zones = df_struct.dropna(subset=['zone_type'])
        end_date = df_struct.index[-1]
        for idx, row in zones.iterrows():
            color = 'rgba(0, 255, 0, 0.2)' if row['zone_type'] == 'DEMAND' else 'rgba(255, 0, 0, 0.2)'
            line_color = 'green' if row['zone_type'] == 'DEMAND' else 'red'
            chart.box(
                start_time=idx, start_value=row['zone_high'],
                end_time=end_date, end_value=row['zone_low'],
                color=line_color, fill_color=color, width=1
            )
        
    # Inside bar zones (pink rectangle)
    inside_zones = identify_inside_bar_zones(df_struct)
    for z in inside_zones:
        start_date = pd.to_datetime(z['start_time']).strftime(time_format)
        end_date = pd.to_datetime(z['end_time']).strftime(time_format)
        chart.box(
            start_time=start_date, start_value=z['high'],
            end_time=end_date, end_value=z['low'],
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
    
    .legend {{ font-size: 20px !important; font-weight: 600 !important; }}
    
    .custom-topbar {{
        position: relative;
        top: 0;
        left: 0;
        right: 0;
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
