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
            
        # Ensure unique timestamps and no zero-interval division errors
        candles_df.drop_duplicates(subset=['time'], inplace=True)
        chart.set(candles_df[['time', 'open', 'high', 'low', 'close']])
        
        if getattr(chart, '_interval', 0) == 0:
            chart._interval = 86400 if not is_intraday else 300
    
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
        height: calc(100vh - 50px - 32px) !important;
    }}
    
    /* Bottom TradingView-style Footer Bar */
    .chart-footer {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 32px;
        background-color: #1e222d;
        border-top: 1px solid #363c4e;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 15px;
        font-size: 12px;
        color: #848e9c;
        user-select: none;
        z-index: 100;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .footer-presets {{ display: flex; gap: 6px; }}
    .footer-btn {{
        background: transparent; border: none; color: #848e9c;
        font-size: 11px; font-weight: 600; cursor: pointer;
        padding: 2px 6px; border-radius: 3px; transition: all 0.15s ease;
    }}
    .footer-btn:hover {{ color: #fff; background: rgba(255, 255, 255, 0.08); }}
    .footer-clock {{ font-family: monospace; color: #848e9c; font-size: 12px; }}
    
    /* Large Hover OHLC Legend */
    #hover-legend {{
        position: absolute;
        top: 65px;
        left: 15px;
        z-index: 1000;
        font-size: 20px !important;
        font-weight: 600 !important;
        font-family: monospace;
        color: #ffffff;
        pointer-events: none;
        background: rgba(19, 23, 34, 0.7);
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid #363c4e;
    }}
    .legend-title {{ font-size: 16px; color: #848e9c; margin-bottom: 4px; }}
    .legend-val {{ margin-right: 12px; }}
    </style>

    <div id="hover-legend" style="display:none;">
        <div class="legend-title" id="legend-symbol">{symbol_raw} - {tf.upper()}</div>
        <div style="font-size:14px; margin-bottom:8px; color:#ff9800;">
            <span id="leg-date">-</span>
        </div>
        <div style="font-size:13px; color:#d1d4dc;">
            O <span class="legend-val" id="leg-o">-</span>
            H <span class="legend-val" id="leg-h">-</span>
            L <span class="legend-val" id="leg-l">-</span>
            C <span class="legend-val" id="leg-c">-</span>
        </div>
    </div>

    <div class="custom-topbar">
        <div class="title">📊 Liquidity Finder</div>
        <a href="/screener" style="margin-right: 15px; color: #fff; text-decoration: none; font-size: 13px; font-weight: 600; background: #2962ff; padding: 4px 10px; border-radius: 4px;">Screener</a>
        
        <div>
            <label style="font-size:12px; color:#848e9c; margin-right:5px;">Market:</label>
            <select id="top-market-select" onchange="changeMarket(this.value)">
                <option value="futures" {"selected" if m_type == "futures" else ""}>Futures</option>
                <option value="equity" {"selected" if m_type == "equity" else ""}>Equity</option>
                <option value="forex" {"selected" if m_type == "forex" else ""}>Forex</option>
                <option value="metals" {"selected" if m_type == "metals" else ""}>Metals</option>
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
    </div>
    
    <!-- Bottom TradingView-style Time Scale Footer -->
    <div class="chart-footer">
        <div class="footer-presets">
            <button class="footer-btn" onclick="fitRange('1d')">1D</button>
            <button class="footer-btn" onclick="fitRange('5d')">5D</button>
            <button class="footer-btn" onclick="fitRange('1m')">1M</button>
            <button class="footer-btn" onclick="fitRange('3m')">3M</button>
            <button class="footer-btn" onclick="fitRange('6m')">6M</button>
            <button class="footer-btn" onclick="fitRange('ytd')">YTD</button>
            <button class="footer-btn" onclick="fitRange('1y')">1Y</button>
            <button class="footer-btn" onclick="fitRange('all')">All</button>
        </div>
        <div class="footer-clock" id="live-clock">--:--:-- UTC+5:30</div>
    </div>

    <script>
    function changeMarket(m) {{
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('type', m);
        urlParams.delete('symbol');
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
    
    // Live Clock Ticker
    setInterval(() => {{
        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        const clockEl = document.getElementById('live-clock');
        if (clockEl) clockEl.innerText = `${{h}}:${{m}}:${{s}} UTC+5:30`;
    }}, 1000);
    
    // Fit range functionality. window.chart doesn't exist by default in StaticLWC
    // But StaticLWC defines window.chart inside its script if we access window.handlers?
    // Actually, lightweight-charts instance is stored somewhere. For simplicity, we just use window.chart = chart in the injected script or leave it.
    """ + r"""
    
    // Attach hover legend to the chart
    setTimeout(() => {
        let chart = null;
        let candleSeries = null;
        
        // Find the chart from window.handlers
        if (window.handlers) {
            const keys = Object.keys(window.handlers);
            if (keys.length > 0) {
                const handler = window.handlers[keys[0]];
                if (handler && handler.chart) {
                    chart = handler.chart;
                    candleSeries = handler.series;
                }
            }
        }
        
        if (chart) {
            document.getElementById('hover-legend').style.display = 'block';
            const urlParams = new URLSearchParams(window.location.search);
            const currentTimeframe = urlParams.get('timeframe') || '1d';
            const mType = urlParams.get('type') || 'futures';
            const decimals = (mType === 'forex' || mType === 'metals') ? 5 : 2;
            
            // Adjust the series price scale for Forex
            if (candleSeries) {
                candleSeries.applyOptions({
                    priceFormat: {
                        type: 'price',
                        precision: decimals,
                        minMove: 1 / Math.pow(10, decimals)
                    }
                });
            }
            
            chart.subscribeCrosshairMove(param => {
                if (!param || !param.time) {
                    document.getElementById('leg-date').innerText = '-';
                    document.getElementById('leg-o').innerText = '-';
                    document.getElementById('leg-h').innerText = '-';
                    document.getElementById('leg-l').innerText = '-';
                    document.getElementById('leg-c').innerText = '-';
                    return;
                }

                let dateStr = "";
                if (typeof param.time === 'number') {
                    const d = new Date(param.time * 1000);
                    const y = d.getUTCFullYear();
                    const m = String(d.getUTCMonth() + 1).padStart(2, '0');
                    const day = String(d.getUTCDate()).padStart(2, '0');
                    const hh = String(d.getUTCHours()).padStart(2, '0');
                    const mm = String(d.getUTCMinutes()).padStart(2, '0');
                    if (currentTimeframe === '1d' || currentTimeframe === '1w') {
                        dateStr = `${y}-${m}-${day}`;
                    } else {
                        dateStr = `${y}-${m}-${day} ${hh}:${mm}`;
                    }
                } else if (typeof param.time === 'object') {
                    const y = param.time.year;
                    const m = String(param.time.month).padStart(2, '0');
                    const day = String(param.time.day).padStart(2, '0');
                    dateStr = `${y}-${m}-${day}`;
                } else {
                    dateStr = String(param.time);
                }
                document.getElementById('leg-date').innerText = dateStr;

                if (param.seriesData) {
                    // Try to get price from seriesData map
                    let price = null;
                    if (candleSeries) {
                        price = param.seriesData.get(candleSeries);
                    }
                    if (!price) {
                        // Fallback if candleSeries not identified: just pick the first available series data
                        const iter = param.seriesData.values();
                        for (let val of iter) {
                            if (val && val.open !== undefined) {
                                price = val;
                                break;
                            }
                        }
                    }
                    if (price) {
                        document.getElementById('leg-o').innerText = price.open ? price.open.toFixed(decimals) : '-';
                        document.getElementById('leg-h').innerText = price.high ? price.high.toFixed(decimals) : '-';
                        document.getElementById('leg-l').innerText = price.low ? price.low.toFixed(decimals) : '-';
                        document.getElementById('leg-c').innerText = price.close ? price.close.toFixed(decimals) : '-';
                    }
                }
            });
        }
    }, 500);
    </script>
    """
    
    # Inject our container resize to the generated lightweight-charts HTML
    # StaticLWC hardcodes window.innerHeight for canvas height, so we must override it
    # to account for our 50px top header + 32px bottom footer = 82px.
    html_fixed = chart._html.replace('window.innerHeight', '(window.innerHeight - 82)')
    
    # Hide the default tiny legend since we added our custom large one
    html_fixed = html_fixed.replace('legend:{', 'legend:{visible:false,')
    
    full_html = f"{html_fixed}</script>{topbar_ui}</body></html>"

    return full_html
