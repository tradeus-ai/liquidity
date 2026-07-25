import logging
from data_fetcher import DataFetcher
from tvDatafeed import Interval
from market_structure import MarketStructureAnalyzer
import mplfinance as mpf
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

def plot_structure(df, filename="chart.png", title="Market Structure"):
    # Focus on the last 100 candles for readability
    df_plot = df.tail(100).copy()
    
    # We will collect lines to draw for structure events (BOS, CHOCH)
    # and horizontal lines for zones.
    hlines = []
    colors = []
    alines = []
    
    events = df_plot.dropna(subset=['structure_event'])
    min_date = df_plot.index[0]
    
    aline_colors = []
    
    for idx, row in events.iterrows():
        if pd.notna(row.get('event_start_idx')):
            start_date = row['event_start_idx']
            end_date = row['event_end_idx']
            start_val = row['event_start_val']
            end_val = row['event_end_val']
            
            if start_date < min_date:
                start_date = min_date
                
            alines.append([(start_date, start_val), (end_date, end_val)])
            aline_colors.append('blue')
            
    # Add pullback line
    pullback_points = []
    last_swing = None  # 'HIGH' or 'LOW'
    
    for idx, row in df_plot.iterrows():
        is_high = row.get('is_swing_high', False)
        is_low = row.get('is_swing_low', False)
        
        if is_high and is_low:
            if last_swing == 'HIGH':
                # Need a LOW first to alternate from previous HIGH
                pullback_points.append((idx, row['low']))
                pullback_points.append((idx, row['high']))
                last_swing = 'HIGH'
            else:
                # Need a HIGH first to alternate from previous LOW
                pullback_points.append((idx, row['high']))
                pullback_points.append((idx, row['low']))
                last_swing = 'LOW'
        elif is_high:
            pullback_points.append((idx, row['high']))
            last_swing = 'HIGH'
        elif is_low:
            pullback_points.append((idx, row['low']))
            last_swing = 'LOW'
            
    if len(pullback_points) > 1:
        alines.append(pullback_points)
        aline_colors.append('orange')
            
    zones = df_plot.dropna(subset=['zone_type'])
    for idx, row in zones.iterrows():
        # Draw a horizontal line for the zone high/low
        hlines.append(row['zone_low'])
        hlines.append(row['zone_high'])
        c = 'green' if row['zone_type'] == 'DEMAND' else 'red'
        colors.extend([c, c])

    kwargs = dict(type='candle', style='charles', title=title, volume=False)
    
    if hlines:
        kwargs['hlines'] = dict(hlines=hlines, colors=colors, linestyle='--', linewidths=1)
    if alines:
        kwargs['alines'] = dict(alines=alines, colors=aline_colors, linestyle='-', linewidths=1)
        
    mpf.plot(df_plot, **kwargs, savefig=filename)
    print(f"Saved plot to {filename}")

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
        plot_structure(df_15m_struct, "chart_15m.png", title=f"{symbol} 15m Structure")
    
    print("\nProcessing 1D fetch...")
    df_1d = fetcher.fetch_data(symbol, exchange, Interval.in_daily, '1d')
    if df_1d is not None:
        # Pass 15m data for outside bar resolution on daily chart
        analyzer_1d = MarketStructureAnalyzer(df_1d, timeframe='1d', ltf_df=df_15m)
        df_1d_struct = analyzer_1d.identify_structure()
        plot_structure(df_1d_struct, "chart_1d.png", title=f"{symbol} 1D Structure")

if __name__ == "__main__":
    main()
