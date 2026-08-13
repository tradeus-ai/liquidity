import os
import json
import pandas as pd
import numpy as np
from tvDatafeed import Interval
from data_fetcher import DataFetcher
from market_structure import MarketStructureAnalyzer
from inside_bars import identify_inside_bar_zones
from bos_choch_inducement import analyze_htf_structure

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fetcher = DataFetcher(data_dir=os.path.join(BASE_DIR, "data"))
CACHE_DIR = os.path.join(BASE_DIR, "data", "structure_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

TIMEFRAME_MAP = {
    '1w': (Interval.in_weekly, '1W'),
    '1d': (Interval.in_daily, '1d'),
    '4h': (Interval.in_4_hour, '4h'),
    '1h': (Interval.in_1_hour, '1h'),
    '15m': (Interval.in_15_minute, '15m'),
    '5m': (Interval.in_5_minute, '5m')
}

LTF_MAP = {
    '1w': '1d',
    '1d': '15m',
    '4h': '15m',
    '1h': '5m',
    '15m': '5m',
    '5m': None
}

def get_chart_data(symbol_raw, timeframe_raw='1d', market_type='futures'):
    tf = timeframe_raw.lower()
    if tf not in TIMEFRAME_MAP:
        tf = '1d'
        
    m_type = str(market_type).lower().strip()
    clean_symbol_raw = symbol_raw.replace('1!', '').strip()
    clean_upper = clean_symbol_raw.upper()
    
    if m_type not in ['forex', 'metals', 'equity']:
        if clean_upper in {'AUDUSD', 'EURUSD', 'USDJPY', 'GBPUSD', 'USDCAD', 'USDCHF', 'NZDUSD'}:
            m_type = 'forex'
        elif clean_upper in {'XAUUSD', 'XAGUSD'}:
            m_type = 'metals'
            
    if m_type == 'equity':
        tv_symbol = clean_symbol_raw
        exchange = 'NSE'
    elif m_type in ['forex', 'metals']:
        tv_symbol = clean_symbol_raw
        exchange = 'PEPPERSTONE'
    else:
        tv_symbol = f"{clean_symbol_raw}1!"
        exchange = 'NSE'
    
    interval_enum, interval_name = TIMEFRAME_MAP[tf]
    
    # Fetch main candle data
    df = fetcher.fetch_data(tv_symbol, exchange, interval_enum, interval_name, n_bars_initial=3000, n_bars_update=500)
    
    if df is None or df.empty:
        return {'error': f'Failed to fetch data for {tv_symbol}'}

    # IMPORTANT: Round data to match market tick precision (prevents floating point errors in swing logic)
    decimals_val = 5 if m_type in ['forex', 'metals'] else 2
    for col in ['open', 'high', 'low', 'close']:
        if col in df.columns:
            df[col] = df[col].round(decimals_val)

    clean_sym = tv_symbol.replace('!', '_')
    cache_path = os.path.join(CACHE_DIR, f"{clean_sym}_{tf}_{m_type}.json")
    
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
        if ltf_df is not None and not ltf_df.empty:
            for col in ['open', 'high', 'low', 'close']:
                if col in ltf_df.columns:
                    ltf_df[col] = ltf_df[col].round(decimals_val)

    analyzer = MarketStructureAnalyzer(df, timeframe=tf, ltf_df=ltf_df)
    df_struct = analyzer.identify_structure()
    
    is_intraday = tf in ['4h', '1h', '15m', '5m']
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
        dt = pd.to_datetime(row['time'])
        ts_val = int(dt.timestamp())
        candles.append({
            'time': ts_val,
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
        dt = pd.to_datetime(idx)
        ts_val = int(dt.timestamp())
        
        if is_high and is_low:
            ts_val2 = ts_val + 1
            if last_swing == 'HIGH':
                # We need a LOW, then a HIGH
                pullback_points.append({'time': ts_val, 'value': float(row['low'])})
                pullback_points.append({'time': ts_val2, 'value': float(row['high'])})
                last_swing = 'HIGH'
            else:
                # We need a HIGH, then a LOW
                pullback_points.append({'time': ts_val, 'value': float(row['high'])})
                pullback_points.append({'time': ts_val2, 'value': float(row['low'])})
                last_swing = 'LOW'
        elif is_high:
            pullback_points.append({'time': ts_val, 'value': float(row['high'])})
            last_swing = 'HIGH'
        elif is_low:
            pullback_points.append({'time': ts_val, 'value': float(row['low'])})
            last_swing = 'LOW'
            
    inside_zones_raw = identify_inside_bar_zones(df_struct)
    inside_zones = []
    for z in inside_zones_raw:
        st_dt = pd.to_datetime(z['start_time'])
        et_dt = pd.to_datetime(z['end_time'])
        inside_zones.append({
            'start_time': int(st_dt.timestamp()),
            'end_time': int(et_dt.timestamp()),
            'high': float(z['high']),
            'low': float(z['low'])
        })
        
    zones = []
    htf_events = []
    htf_zones = []
    current_state = {}
    
    # Analyze Market Structure (BOS, ChoCH, Inducement) for all timeframes
    res = analyze_htf_structure(df_struct)
    raw_events = res['events']
    raw_zones = res['zones']
    current_state = res.get('current_state', {})
    
    for ev in raw_events:
        dt_st = pd.to_datetime(ev['start_time'])
        dt_et = pd.to_datetime(ev['end_time'])
        htf_events.append({
            'type': ev['type'],
            'label': ev['label'],
            'start_time': int(dt_st.timestamp()),
            'start_val': float(ev['start_val']),
            'end_time': int(dt_et.timestamp()),
            'end_val': float(ev['end_val']),
            'color': ev['color']
        })
        
    htf_zones = []
    # for z in res.get('zones', []):
    #     # Only include active zones (still visible on chart)
    #     if z.get('status') != 'active':
    #         continue
    #     dt_st = pd.to_datetime(z['start_time'])
    #     dt_et = pd.to_datetime(z.get('end_time', df.index[-1]))
    #     htf_zones.append({
    #         'type': z['type'],
    #         'start_time': int(dt_st.timestamp()),
    #         'end_time': int(dt_et.timestamp()),
    #         'top': float(z['top']),
    #         'bottom': float(z['bottom']),
    #         'status': z.get('status', 'active')
    #     })
        
    payload = {
        'symbol': symbol_raw,
        'timeframe': tf,
        'is_intraday': is_intraday,
        'candles': candles,
        'pullback_points': pullback_points,
        'inside_zones': inside_zones,
        'zones': zones,
        'htf_events': htf_events,
        'htf_zones': htf_zones,
        'current_state': current_state
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
