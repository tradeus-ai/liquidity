import pandas as pd
import numpy as np
from tvDatafeed import Interval
from data_fetcher import DataFetcher
from market_structure import MarketStructureAnalyzer
from inside_bars import identify_inside_bar_zones

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

def get_chart_data(symbol_raw, timeframe_raw='1d'):
    tf = timeframe_raw.lower()
    if tf not in TIMEFRAME_MAP:
        tf = '1d'
        
    tv_symbol = f"{symbol_raw}1!" if not symbol_raw.endswith('1!') else symbol_raw
    exchange = 'NSE'
    
    interval_enum, interval_name = TIMEFRAME_MAP[tf]
    
    # Check if we need LTF data for outside bar resolution
    ltf_name = LTF_MAP.get(tf)
    ltf_df = None
    if ltf_name and ltf_name in TIMEFRAME_MAP:
        ltf_enum, ltf_str = TIMEFRAME_MAP[ltf_name]
        ltf_df = fetcher.fetch_data(tv_symbol, exchange, ltf_enum, ltf_str, n_bars_initial=2000, n_bars_update=300)
        
    df = fetcher.fetch_data(tv_symbol, exchange, interval_enum, interval_name, n_bars_initial=3000, n_bars_update=500)
    
    if df is None or df.empty:
        return {'error': f'Failed to fetch data for {tv_symbol}'}
        
    analyzer = MarketStructureAnalyzer(df, timeframe=tf, ltf_df=ltf_df)
    df_struct = analyzer.identify_structure()
    
    # Format time column for JS
    is_intraday = tf in ['1h', '15m', '5m']
    time_format = '%Y-%m-%d %H:%M:%S' if is_intraday else '%Y-%m-%d'
    
    df_plot = df_struct.copy()
    if pd.api.types.is_datetime64_any_dtype(df_plot.index):
        df_plot.index = df_plot.index.strftime(time_format)
        
    if df_plot.index.name != 'time':
        df_plot = df_plot.reset_index()
        df_plot.rename(columns={df_plot.columns[0]: 'time'}, inplace=True)
        
    df_plot.columns = [c.lower() for c in df_plot.columns]
    
    # Convert timestamps to nanoseconds datetime for unix seconds conversion
    candles = []
    for _, row in df_plot.iterrows():
        # Unix timestamp in seconds
        ts = int(pd.to_datetime(row['time']).timestamp())
        candles.append({
            'time': ts,
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close'])
        })
        
    # Extract pullback lines
    pullback_points = []
    last_swing = None
    for idx, row in df_struct.iterrows():
        is_high = row.get('is_swing_high', False)
        is_low = row.get('is_swing_low', False)
        date_str = pd.to_datetime(idx).strftime(time_format)
        ts = int(pd.to_datetime(date_str).timestamp())
        
        if is_high and is_low:
            if last_swing == 'HIGH':
                pullback_points.append({'time': ts, 'value': float(row['low'])})
                pullback_points.append({'time': ts, 'value': float(row['high'])})
                last_swing = 'HIGH'
            else:
                pullback_points.append({'time': ts, 'value': float(row['high'])})
                pullback_points.append({'time': ts, 'value': float(row['low'])})
                last_swing = 'LOW'
        elif is_high:
            pullback_points.append({'time': ts, 'value': float(row['high'])})
            last_swing = 'HIGH'
        elif is_low:
            pullback_points.append({'time': ts, 'value': float(row['low'])})
            last_swing = 'LOW'
            
    # Extract inside bar boxes
    inside_zones_raw = identify_inside_bar_zones(df_struct)
    inside_zones = []
    for z in inside_zones_raw:
        st_str = pd.to_datetime(z['start_time']).strftime(time_format)
        et_str = pd.to_datetime(z['end_time']).strftime(time_format)
        inside_zones.append({
            'start_time': int(pd.to_datetime(st_str).timestamp()),
            'end_time': int(pd.to_datetime(et_str).timestamp()),
            'high': float(z['high']),
            'low': float(z['low'])
        })
        
    # Extract demand/supply zones (ONLY for Higher Timeframe Daily - 1D)
    zones = []
    if tf == '1d':
        zones_df = df_struct.dropna(subset=['zone_type'])
        end_ts = int(pd.to_datetime(df_struct.index[-1]).timestamp())
        for idx, row in zones_df.iterrows():
            st_ts = int(pd.to_datetime(idx).timestamp())
            zones.append({
                'type': str(row['zone_type']),
                'start_time': st_ts,
                'end_time': end_ts,
                'high': float(row['zone_high']),
                'low': float(row['zone_low'])
            })
        
    return {
        'symbol': symbol_raw,
        'timeframe': tf,
        'is_intraday': is_intraday,
        'candles': candles,
        'pullback_points': pullback_points,
        'inside_zones': inside_zones,
        'zones': zones
    }
