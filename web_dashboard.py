import os
import pandas as pd
from symbol_loader import get_symbol_list
from structure_service import get_chart_data
from lightweight_charts.widgets import StaticLWC

def render_dashboard(symbol_raw="AMBUJACEM", timeframe_raw="1d", market_type_raw="futures"):
    tf = timeframe_raw.lower()
    m_type = str(market_type_raw).lower().strip()
    data = get_chart_data(symbol_raw, tf, m_type)
    
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
    
    # Format candle dataframe for lightweight-charts safely
    candles_df = pd.DataFrame(data['candles'])
    if not candles_df.empty:
        if is_intraday:
            candles_df['time'] = pd.to_datetime(candles_df['time'], unit='s').astype('datetime64[ns]')
        else:
            candles_df['time'] = pd.to_datetime(candles_df['time']).astype('datetime64[ns]')
        chart.set(candles_df[['time', 'open', 'high', 'low', 'close']])
    
    # Add pullback line safely
    if len(data.get('pullback_points', [])) > 1:
        line_df = pd.DataFrame(data['pullback_points'])
        if is_intraday:
            line_df['time'] = pd.to_datetime(line_df['time'], unit='s').astype('datetime64[ns]')
        else:
            line_df['time'] = pd.to_datetime(line_df['time']).astype('datetime64[ns]')
        line = chart.create_line(color='#ff9800', width=3)
        line.set(line_df)
        
    # Helper to parse scalar time
    def format_time_scalar(val, fmt='%Y-%m-%d'):
        if isinstance(val, (int, float)):
            return pd.to_datetime(val, unit='s').strftime(fmt)
        return str(val)

    # HTF Structure Events (#, IS, BOS, ChoCH) - ONLY for Daily - 1D
    if tf == '1d':
        for ev in data.get('htf_events', []):
            st_date = format_time_scalar(ev['start_time'])
            et_date = format_time_scalar(ev['end_time'])
            chart.trend_line(
                start_time=st_date, start_value=ev['start_val'],
                end_time=et_date, end_value=ev['end_val'],
                line_color=ev['color'], width=2, style='solid'
            )

    # Inside bar zones (pink rectangle)
    time_fmt = '%Y-%m-%d %H:%M:%S' if is_intraday else '%Y-%m-%d'
    for z in data.get('inside_zones', []):
        st_date = format_time_scalar(z['start_time'], time_fmt)
        et_date = format_time_scalar(z['end_time'], time_fmt)
        chart.box(
            start_time=st_date, start_value=z['high'],
            end_time=et_date, end_value=z['low'],
            color='pink', fill_color='rgba(255, 105, 180, 0.2)', width=1
        )
        
    chart.load()
    
    # Symbols dropdown options based on market type
    symbols = get_symbol_list(m_type)
    clean_sym_raw = symbol_raw.replace('1!', '')
    symbol_options = "".join(f'<option value="{s}" {"selected" if s == clean_sym_raw else ""}>{s}</option>' for s in symbols)
    
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
        <a href="/screener" style="margin-right: 15px; color: #fff; text-decoration: none; font-size: 13px; font-weight: 600; background: #2962ff; padding: 4px 10px; border-radius: 4px;">Screener</a>
        
        <div>
            <label style="font-size:12px; color:#848e9c; margin-right:5px;">Market:</label>
            <select id="top-market-select" onchange="changeMarket(this.value)">
                <option value="futures" {"selected" if m_type == "futures" else ""}>Futures</option>
                <option value="equity" {"selected" if m_type == "equity" else ""}>Equity</option>
            </select>
        </div>

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

    <script>
    function changeMarket(m) {{
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('type', m);
        window.location.search = urlParams.toString();
    }}
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
    </script>
    """
    
    full_html = f"{chart._html}</script>{topbar_ui}</body></html>"
    return full_html
