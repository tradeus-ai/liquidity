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
    forex_metals_list = ['AUDUSD', 'EURUSD', 'USDJPY', 'GBPUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'XAUUSD', 'XAGUSD']
    clean_sym_upper = str(symbol_raw).upper().replace('1!', '').strip()
    is_forex_metals = (m_type in ['forex', 'metals']) or (clean_sym_upper in forex_metals_list)
    decimals_val = 5 if is_forex_metals else 2

    chart.time_scale(time_visible=is_intraday, seconds_visible=False)
    chart.legend(visible=True, ohlc=True, percent=True, font_size=20)
    if is_forex_metals:
        chart.precision(5)
    
    # Force the JS handler to use the correct precision for the legend OHLC formatting
    chart.run_script(f"{chart.id}.precision = {decimals_val};")

    # Add custom candle strength overlay on hover
    chart.run_script(f"""
        let strengthContainer = document.createElement('div');
        strengthContainer.style.position = 'absolute';
        strengthContainer.style.top = '50px';
        strengthContainer.style.left = '12px';
        strengthContainer.style.zIndex = '1000';
        strengthContainer.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif';
        strengthContainer.style.fontSize = '14px';
        strengthContainer.style.pointerEvents = 'none';
        document.body.appendChild(strengthContainer);

        {chart.id}.chart.subscribeCrosshairMove((param) => {{
            if (!param.time || !param.seriesData) {{
                strengthContainer.innerHTML = '';
                return;
            }}
            let data = param.seriesData.get({chart.id}.series);
            if (data) {{
                let high = data.high;
                let low = data.low;
                let close = data.close;
                let range = high - low;
                let sellers = range === 0 ? 0 : ((high - close) / range) * 100;
                let buyers = range === 0 ? 0 : ((close - low) / range) * 100;
                strengthContainer.innerHTML = `
                    <div style="display: flex; gap: 15px; background: rgba(19, 23, 34, 0.8); padding: 4px 8px; border-radius: 4px;">
                        <span style="color: #4caf50; font-weight: bold;">Buyers: ${{buyers.toFixed(5)}}%</span>
                        <span style="color: #f44336; font-weight: bold;">Sellers: ${{sellers.toFixed(5)}}%</span>
                    </div>
                `;
            }} else {{
                strengthContainer.innerHTML = '';
            }}
        }});
    """)
    # Format candle dataframe for lightweight-charts safely
    candles_df = pd.DataFrame(data['candles'])
    if pd.api.types.is_numeric_dtype(candles_df['time']):
        candles_df['time'] = pd.to_datetime(candles_df['time'], unit='s').astype('datetime64[ns]')
    else:
        candles_df['time'] = pd.to_datetime(candles_df['time']).astype('datetime64[ns]')
    if not candles_df.empty:
        # Ensure unique timestamps and no zero-interval division errors
        candles_df.drop_duplicates(subset=['time'], inplace=True)
        chart.set(candles_df[['time', 'open', 'high', 'low', 'close']])
        
        # Override internal library interval quantization so event timestamps aren't floored.
        # _set_interval (called inside chart.set) computes _interval AND offset from candle diffs.
        # _single_datetime_format does: _interval * (ts // _interval) + offset
        # For NSE data (09:15 start), offset=900 shifts all events by 15min to non-existent times.
        # Setting both to identity values ensures exact timestamp passthrough.
        chart._interval = 1
        chart.offset = 0
    
    # Add pullback line safely
    if data.get('pullback_points'):
        line_df = pd.DataFrame(data['pullback_points'])
        if pd.api.types.is_numeric_dtype(line_df['time']):
            line_df['time'] = pd.to_datetime(line_df['time'], unit='s').astype('datetime64[ns]')
        else:
            line_df['time'] = pd.to_datetime(line_df['time']).astype('datetime64[ns]')
        line_df.drop_duplicates(subset=['time'], keep='last', inplace=True)
        line = chart.create_line(color='#ff9800', width=3)
        line.set(line_df)
        
    # HTF Structure Events (#, IS, BOS, ChoCH) - FOR ALL TIMEFRAMES
    def parse_dt(ts):
        if isinstance(ts, (int, float)) or (isinstance(ts, str) and str(ts).replace('.','',1).isdigit()):
            dt = pd.to_datetime(float(ts), unit='s')
        else:
            dt = pd.to_datetime(ts)
        if not is_intraday:
            dt = dt.normalize()
        return dt

    htf_js_events_str = "[]"
    events_for_js = []
    for ev in data.get('htf_events', []):
        st_date = parse_dt(ev['start_time'])
        et_date = parse_dt(ev['end_time'])
        chart.trend_line(
            start_time=st_date, start_value=ev['start_val'],
            end_time=et_date, end_value=ev['end_val'],
            line_color=ev['color'], width=2, style='solid'
        )
        # Format time for JS injection
        js_start = chart._single_datetime_format(st_date)
        js_end = chart._single_datetime_format(et_date)
        events_for_js.append(f"{{start_time: {js_start}, end_time: {js_end}, price: {ev['start_val']}, text: '{ev['label']}', color: '{ev['color']}'}}")
    htf_js_events_str = "[" + ",\n".join(events_for_js) + "]"

    # Inside bar zones (pink rectangle)
    for z in data.get('inside_zones', []):
        st_date = parse_dt(z['start_time'])
        et_date = parse_dt(z['end_time'])
        chart.box(
            start_time=st_date, start_value=z['high'],
            end_time=et_date, end_value=z['low'],
            color='pink', fill_color='rgba(255, 105, 180, 0.2)', width=1
        )
    
    # Supply/Demand zones (teal for demand, red for supply) - DISABLED
    # for z in data.get('htf_zones', []):
    #     st_date = parse_dt(z['start_time'])
    #     et_date = parse_dt(z['end_time'])
    #     if z['type'] == 'demand':
    #         box_color = 'rgba(38, 166, 154, 0.6)'
    #         fill_color = 'rgba(38, 166, 154, 0.15)'
    #     else:
    #         box_color = 'rgba(239, 83, 80, 0.6)'
    #         fill_color = 'rgba(239, 83, 80, 0.15)'
    #     chart.box(
    #         start_time=st_date, start_value=z['top'],
    #         end_time=et_date, end_value=z['bottom'],
    #         color=box_color, fill_color=fill_color, width=1
    #     )
        
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
    
    /* Loader CSS */
    #full-page-loader {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(19, 23, 34, 0.9);
        z-index: 10000;
        display: none;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #d1d4dc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .spinner {{
        width: 40px;
        height: 40px;
        border: 4px solid rgba(255, 255, 255, 0.1);
        border-left-color: #2962ff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }}
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    .loader-text {{
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 8px;
    }}
    .loader-subtext {{
        font-size: 13px;
        color: #848e9c;
    }}
    </style>

    <div id="full-page-loader">
        <div class="spinner"></div>
        <div class="loader-text">Loading...</div>
        <div class="loader-subtext">Fetching data, processing pullbacks & market structure</div>
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
            <button class="tf-btn {'active' if tf=='4h' else ''}" onclick="changeTF('4h')">4H</button>
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
    function showLoader() {{
        const loader = document.getElementById('full-page-loader');
        if (loader) loader.style.display = 'flex';
    }}
    function changeMarket(m) {{
        showLoader();
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('type', m);
        urlParams.delete('symbol');
        window.location.search = urlParams.toString();
    }}
    function changeSymbol(sym) {{
        showLoader();
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('symbol', sym);
        window.location.search = urlParams.toString();
    }}
    function changeTF(tf) {{
        showLoader();
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
    
    // Injected from Python
    const PYTHON_DECIMALS = {decimals_val};
    
    """ + r"""
    
    // Attach hover legend and midpoint labels using the actual chart handler
    setTimeout(() => {
        // StaticLWC stores chart as window.<random_id> — use the injected ID
        const lwHandler = """ + chart.id + r""";
        if (!lwHandler) return;
        
        const lwChart = lwHandler.chart;
        const lwSeries = lwHandler.series;
        
        if (!lwChart || !lwSeries) return;
        
        // Scroll to the most recent candle
        lwChart.timeScale().scrollToRealTime();
        
        const urlParams = new URLSearchParams(window.location.search);
        const currentTimeframe = urlParams.get('timeframe') || '1d';
        
        const decimals = PYTHON_DECIMALS;
        
        // Adjust the series price scale for Forex and Metals
        lwSeries.applyOptions({
            priceFormat: {
                type: 'price',
                precision: decimals,
                minMove: 1 / Math.pow(10, decimals)
            }
        });
        
        // ===== Midpoint Labels for HTF Events (Inducement, IS, BOS, ChoCH) =====
        const htfEvents = """ + htf_js_events_str + r""";
        if (htfEvents.length > 0) {
            // lwHandler.div has position:relative — perfect for absolute label positioning
            const container = lwHandler.div;
            
            htfEvents.forEach(ev => {
                let div = document.createElement('div');
                div.innerText = ev.text;
                div.style.position = 'absolute';
                div.style.color = ev.color;
                div.style.backgroundColor = '#131722'; // Match chart background
                div.style.padding = '0px 5px';
                div.style.fontSize = '11px';
                div.style.fontWeight = 'bold';
                div.style.fontFamily = 'Monaco, monospace';
                div.style.zIndex = '100';
                div.style.pointerEvents = 'none';
                div.style.whiteSpace = 'nowrap';
                div.style.lineHeight = '1';
                container.appendChild(div);
                ev.div = div;
            });
            
            function updateLabels() {
                htfEvents.forEach(ev => {
                    try {
                        let x1 = lwChart.timeScale().timeToCoordinate(ev.start_time);
                        let x2 = lwChart.timeScale().timeToCoordinate(ev.end_time);
                        let y = lwSeries.priceToCoordinate(ev.price);
                        
                        if (x1 !== null && x2 !== null && y !== null) {
                            let midX = (x1 + x2) / 2;
                            ev.div.style.left = midX + 'px';
                            ev.div.style.top = y + 'px';
                            ev.div.style.transform = 'translate(-50%, -50%)';
                            ev.div.style.display = 'block';
                        } else {
                            ev.div.style.display = 'none';
                        }
                    } catch (e) {
                        ev.div.style.display = 'none';
                    }
                });
            }
            
            lwChart.timeScale().subscribeVisibleLogicalRangeChange(updateLabels);
            lwChart.timeScale().subscribeVisibleTimeRangeChange(updateLabels);
            // Initial render + periodic update for resize/pan
            updateLabels();
            setInterval(updateLabels, 50);
        }
    }, 500);
    </script>
    """
    
    # Inject our container resize to the generated lightweight-charts HTML
    # StaticLWC hardcodes window.innerHeight for canvas height, so we must override it
    # to account for our 50px top header + 32px bottom footer = 82px.
    html_fixed = chart._html.replace('window.innerHeight', '(window.innerHeight - 82)')
    
    # We use the built-in legend now, no need to hide it
    
    full_html = f"{html_fixed}</script>{topbar_ui}</body></html>"

    return full_html
