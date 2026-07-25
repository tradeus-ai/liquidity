import logging
from data_fetcher import DataFetcher
from tvDatafeed import Interval
from market_structure import MarketStructureAnalyzer
import pandas as pd
import os

# Configure logging for SMC pullback module
# INFO  = shows outside bars + swing confirmations
# DEBUG = shows every single candle comparison
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s | %(message)s'
)
# Set smc_pullback logger to INFO (change to DEBUG for full candle-by-candle logs)
logging.getLogger('smc_pullback').setLevel(logging.INFO)

from lightweight_charts.widgets import StaticLWC

def plot_structure(df, filename="chart", title="Market Structure"):
    is_intraday = '15m' in title.lower()
    time_format = '%Y-%m-%d %H:%M:%S' if is_intraday else '%Y-%m-%d'
    
    # Convert index to string to avoid timezone/unix timestamp bugs in lightweight-charts drawings
    if pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = df.index.strftime(time_format)
        
    df_plot = df.copy()
    
    # Format df for lightweight-charts
    if df_plot.index.name != 'time':
        df_plot = df_plot.reset_index()
        # Rename datetime column to time
        df_plot.rename(columns={df_plot.columns[0]: 'time'}, inplace=True)
    
    # Ensure column names are lowercase for lightweight-charts
    df_plot.columns = [c.lower() for c in df_plot.columns]
    
    # Use StaticLWC to generate a standalone HTML file (avoids PyWebView OS GUI dependencies)
    chart = StaticLWC(toolbox=True)
    
    # Dark mode background with solid white candles
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
    
    # Enable OHLC legend for every candle on hover
    chart.legend(visible=True, ohlc=True, percent=True)
    
    # Convert time column to datetime64[ns] so lightweight_charts converts it to accurate Unix timestamp seconds
    df_plot['time'] = pd.to_datetime(df_plot['time']).astype('datetime64[ns]')

    # Lightweight charts expects exactly time, open, high, low, close, volume (optional)
    chart.set(df_plot[['time', 'open', 'high', 'low', 'close']])
    
    # Add pullback line
    pullback_points = []
    last_swing = None  # 'HIGH' or 'LOW'
    
    for idx, row in df.iterrows():
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
            
    # Add structure events (BOS, CHOCH)
    events = df.dropna(subset=['structure_event'])
    min_date = df.index[0]
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
            
    # Add zones
    zones = df.dropna(subset=['zone_type'])
    end_date = df.index[-1]
    for idx, row in zones.iterrows():
        color = 'rgba(0, 255, 0, 0.2)' if row['zone_type'] == 'DEMAND' else 'rgba(255, 0, 0, 0.2)'
        line_color = 'green' if row['zone_type'] == 'DEMAND' else 'red'
        chart.box(
            start_time=idx, start_value=row['zone_high'],
            end_time=end_date, end_value=row['zone_low'],
            color=line_color, fill_color=color, width=1
        )
        
    # Add inside bar zones (pink rectangle)
    from inside_bars import identify_inside_bar_zones
    inside_zones = identify_inside_bar_zones(df)
    for z in inside_zones:
        start_date = pd.to_datetime(z['start_time']).strftime(time_format)
        end_date = pd.to_datetime(z['end_time']).strftime(time_format)
        chart.box(
            start_time=start_date, start_value=z['high'],
            end_time=end_date, end_value=z['low'],
            color='pink', fill_color='rgba(255, 105, 180, 0.2)', width=1
        )

    # Save to standalone HTML file
    chart.load()
    
    feedback_ui = """
    <div id="feedback-panel" style="position:fixed; bottom:20px; right:20px; z-index:10000; background:#1e222d; color:#d1d4dc; padding:15px; border-radius:8px; border: 1px solid #434651; box-shadow: 0 4px 6px rgba(0,0,0,0.3); font-family: sans-serif; width: 300px;">
       <h3 style="margin-top:0; color:#fff;">Correction Feedback</h3>
       <p style="font-size:12px; margin-bottom:10px;">Use the toolbox to draw lines/boxes, then describe the mistake below to send to the AI.</p>
       <textarea id="feedback-text" rows="4" style="width:100%; background:#131722; color:#fff; border:1px solid #434651; border-radius:4px; padding:5px; margin-bottom:5px;" placeholder="E.g., Missing swing low at 2026-07-21 14:15..."></textarea>
       <button onclick="sendFeedback()" style="width:100%; background:#2962ff; color:#fff; border:none; padding:8px; border-radius:4px; cursor:pointer; font-weight:bold;">Send Feedback</button>
    </div>
    <script>
    function sendFeedback() {
        const text = document.getElementById('feedback-text').value;
        const btn = document.querySelector('button[onclick="sendFeedback()"]');
        
        // Try to capture any drawings from local storage if available
        let drawings = null;
        try {
            // Lightweight charts python saves under a specific key if toolbox is used
            for (let i = 0; i < localStorage.length; i++) {
                let key = localStorage.key(i);
                if (key.includes('drawings')) {
                    drawings = JSON.parse(localStorage.getItem(key));
                }
            }
        } catch(e) {}

        const payload = {
            chart: '""" + filename + """',
            timestamp: new Date().toISOString(),
            description: text,
            drawings: drawings
        };

        btn.innerText = "Sending...";
        fetch('http://127.0.0.1:8080/feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(res => {
            if(res.ok) {
                btn.innerText = "✅ Sent!";
                btn.style.background = "#089981";
                setTimeout(() => { btn.innerText = "Send Feedback"; btn.style.background = "#2962ff"; }, 2000);
            } else {
                alert("Error: Is feedback_server.py running?");
                btn.innerText = "Send Feedback";
            }
        }).catch(err => {
            alert("Connection failed! Make sure you run 'python feedback_server.py' in a separate terminal.");
            btn.innerText = "Send Feedback";
        });
    }
    </script>
    """
    
    with open(f"{filename}.html", "w", encoding="utf-8") as f:
        f.write(f"{chart._html}</script>{feedback_ui}</body></html>")
        
    print(f"Saved interactive chart to {filename}.html")

def main():
    fetcher = DataFetcher(data_dir="data")
    symbol = 'AMBUJACEM1!'
    exchange = 'NSE'
    
    # Fetch 15m data first — used as LTF for resolving daily outside bars
    print("\nProcessing 15m fetch...")
    df_15m = fetcher.fetch_data(symbol, exchange, Interval.in_15_minute, '15m')
    if df_15m is not None:
        analyzer_15m = MarketStructureAnalyzer(df_15m, timeframe='15m')
        df_15m_struct = analyzer_15m.identify_structure()
        plot_structure(df_15m_struct, "chart_15m", title=f"{symbol} 15m Structure")
    
    print("\nProcessing 1D fetch...")
    df_1d = fetcher.fetch_data(symbol, exchange, Interval.in_daily, '1d')
    if df_1d is not None:
        # Pass 15m data for outside bar resolution on daily chart
        analyzer_1d = MarketStructureAnalyzer(df_1d, timeframe='1d', ltf_df=df_15m)
        df_1d_struct = analyzer_1d.identify_structure()
        plot_structure(df_1d_struct, "chart_1d", title=f"{symbol} 1D Structure")

if __name__ == "__main__":
    main()
