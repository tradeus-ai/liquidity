import os
import json
import pandas as pd
import numpy as np
from tvDatafeed import Interval
from data_fetcher import DataFetcher
from market_structure import MarketStructureAnalyzer
from inside_bars import identify_inside_bar_zones

fetcher = DataFetcher(data_dir="data")
CACHE_DIR = "data/structure_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

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
    
    # Fetch main candle data
    df = fetcher.fetch_data(tv_symbol, exchange, interval_enum, interval_name, n_bars_initial=3000, n_bars_update=500)
    
    if df is None or df.empty:
        return {'error': f'Failed to fetch data for {tv_symbol}'}

    clean_sym = tv_symbol.replace('!', '_')
    cache_path = os.path.join(CACHE_DIR, f"{clean_sym}_{tf}.json")
    
    last_candle_time = int(pd.to_datetime(df.index[-1]).timestamp())
    total_candles = len(df)
    
    # Check structure cache
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            if cached_data.get('last_timestamp') == last_candle_time and cached_data.get('total_candles') == total_candles:
                print(f"⚡ Cache Hit: Loaded structure for {tv_symbol} ({tf}) instantly!")
                return cached_data['payload']
        except Exception as e:
            print(f"⚠️ Cache read failed for {tv_symbol} ({tf}): {e}")

    print(f"🔄 Cache Miss: Computing SMC Structure & Pullbacks for {tv_symbol} ({tf})...")

    # Check if we need LTF data for outside bar resolution
    ltf_name = LTF_MAP.get(tf)
    ltf_df = None
    if ltf_name and ltf_name in TIMEFRAME_MAP:
        ltf_enum, ltf_str = TIMEFRAME_MAP[ltf_name]
        ltf_df = fetcher.fetch_data(tv_symbol, exchange, ltf_enum, ltf_str, n_bars_initial=2000, n_bars_update=300)
        
    analyzer = MarketStructureAnalyzer(df, timeframe=tf, ltf_df=ltf_df)
    df_struct = analyzer.identify_structure()
    
    is_intraday = tf in ['1h', '15m', '5m']
    time_format = '%Y-%m-%d %H:%M:%S' if is_intraday else '%Y-%m-%d'
    
    df_plot = df_struct.copy()
    if pd.api.types.is_datetime64_any_dtype(df_plot.index):
        df_plot.index = df_plot.index.strftime(time_format)
        
    if df_plot.index.name != 'time':
        df_plot = df_plot.reset_index()
        df_plot.rename(columns={df_plot.columns[0]: 'time'}, inplace=True)
        
    df_plot.columns = [c.lower() for c in df_plot.columns]
    
    candles = []
    for _, row in df_plot.iterrows():
        ts = int(pd.to_datetime(row['time']).timestamp())
        candles.append({
            'time': ts,
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close'])
        })
        
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
        
    payload = {
        'symbol': symbol_raw,
        'timeframe': tf,
        'is_intraday': is_intraday,
        'candles': candles,
        'pullback_points': pullback_points,
        'inside_zones': inside_zones,
        'zones': zones
    }
    
    # Write to cache
    try:
        cache_entry = {
            'last_timestamp': last_candle_time,
            'total_candles': total_candles,
            'payload': payload
        }
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_entry, f)
        print(f"💾 Structure cached to {cache_path}")
    except Exception as e:
        print(f"⚠️ Failed to write cache for {tv_symbol} ({tf}): {e}")
        
    return payload
