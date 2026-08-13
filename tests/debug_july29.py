"""
Precise diagnostic: trace smc_pullback logic for AXISBANK July 22-31.
Shows what is_swing_high / is_swing_low flags the engine produces,
and what the structure_service extraction loop converts them into.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from data_fetcher import DataFetcher
from market_structure import MarketStructureAnalyzer
from smc_pullback import round_price
from tvDatafeed import Interval

fetcher = DataFetcher(data_dir="data")
df = fetcher.fetch_data("AXISBANK1!", "NSE", Interval.in_daily, "1d",
                        n_bars_initial=3000, n_bars_update=500)
for col in ['open','high','low','close']:
    df[col] = df[col].round(2)

# Run structure analysis (which calls find_swings internally)
analyzer = MarketStructureAnalyzer(df, timeframe='1d', ltf_df=None)
df_struct = analyzer.identify_structure()

print("=== SWING FLAGS produced by smc_pullback.py ===")
for idx, row in df_struct.iterrows():
    ds = pd.to_datetime(idx).strftime('%Y-%m-%d')
    if '2026-07-22' <= ds <= '2026-08-05':
        sh = row.get('is_swing_high', False)
        sl = row.get('is_swing_low', False)
        flag = ""
        if sh and sl: flag = "*** BOTH ***"
        elif sh: flag = "SWING HIGH"
        elif sl: flag = "SWING LOW"
        if flag:
            print(f"  {ds} H={row['high']:.2f} L={row['low']:.2f} => {flag}")

print("\n=== PULLBACK POINTS from structure_service extraction ===")
# Simulate the extraction logic from structure_service.py
pullback_points = []
last_swing = None
is_intraday = False

for idx, row in df_struct.iterrows():
    is_high = row.get('is_swing_high', False)
    is_low = row.get('is_swing_low', False)
    dt = pd.to_datetime(idx)
    ts_val = dt.strftime('%Y-%m-%d')
    ds = ts_val
    
    if is_high and is_low:
        ts_val2 = ts_val  # daily mode
        if last_swing == 'HIGH':
            pullback_points.append({'time': ts_val, 'value': float(row['low']), 'type': 'LOW'})
            pullback_points.append({'time': ts_val2, 'value': float(row['high']), 'type': 'HIGH'})
            last_swing = 'HIGH'
        else:
            pullback_points.append({'time': ts_val, 'value': float(row['high']), 'type': 'HIGH'})
            pullback_points.append({'time': ts_val2, 'value': float(row['low']), 'type': 'LOW'})
            last_swing = 'LOW'
    elif is_high:
        pullback_points.append({'time': ts_val, 'value': float(row['high']), 'type': 'HIGH'})
        last_swing = 'HIGH'
    elif is_low:
        pullback_points.append({'time': ts_val, 'value': float(row['low']), 'type': 'LOW'})
        last_swing = 'LOW'

for p in pullback_points:
    if '2026-07-22' <= p['time'] <= '2026-08-05':
        print(f"  {p['time']} => {p['type']} value={p['value']:.2f}")

print("\n=== Now trace smc_pullback STEP BY STEP for July 22-31 ===")
# Manual trace
opens = [round_price(v) for v in df['open'].values]
highs = [round_price(v) for v in df['high'].values]
lows  = [round_price(v) for v in df['low'].values]

current_dir = 0
swing_high_idx = 0; swing_high_val = highs[0]
swing_low_idx = 0; swing_low_val = lows[0]
ref_high = highs[0]; ref_low = lows[0]

def date_of(i):
    return pd.to_datetime(df.index[i]).strftime('%Y-%m-%d')

# Process all bars silently up to July 21
for i in range(1, len(df)):
    ds = date_of(i)
    if ds >= '2026-07-22':
        break
    curr_open = opens[i]; curr_high = highs[i]; curr_low = lows[i]
    open_broke_high = curr_open > ref_high
    open_broke_low = curr_open < ref_low
    broke_high = (curr_high > ref_high) or open_broke_high
    broke_low = (curr_low < ref_low) or open_broke_low
    if broke_high or broke_low:
        if broke_high and broke_low:
            tf = 0
            if open_broke_high: tf = 1
            elif open_broke_low: tf = -1
            else:
                dh = abs(curr_open - ref_high); dl = abs(curr_open - ref_low)
                tf = -1 if dl < dh else 1
            if tf == 1:
                # up then down
                if current_dir == -1:
                    current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
                elif current_dir == 1:
                    if curr_high >= swing_high_val: swing_high_idx = i; swing_high_val = curr_high
                else:
                    current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
                if current_dir == 1:
                    current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
                elif current_dir == -1:
                    if curr_low <= swing_low_val: swing_low_idx = i; swing_low_val = curr_low
                else:
                    current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
            else:
                # down then up
                if current_dir == 1:
                    current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
                elif current_dir == -1:
                    if curr_low <= swing_low_val: swing_low_idx = i; swing_low_val = curr_low
                else:
                    current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
                if current_dir == -1:
                    current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
                elif current_dir == 1:
                    if curr_high >= swing_high_val: swing_high_idx = i; swing_high_val = curr_high
                else:
                    current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
        else:
            if current_dir == 1:
                if broke_low:
                    current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
                elif broke_high:
                    if curr_high >= swing_high_val: swing_high_idx = i; swing_high_val = curr_high
            elif current_dir == -1:
                if broke_high:
                    current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
                elif broke_low:
                    if curr_low <= swing_low_val: swing_low_idx = i; swing_low_val = curr_low
            else:
                if broke_high: current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
                elif broke_low: current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
        ref_high = curr_high; ref_low = curr_low

# Now trace verbose for July 22 - Aug 5
start_i = i
print(f"\nState entering July 22:")
print(f"  current_dir={current_dir}")
print(f"  ref_high={ref_high}, ref_low={ref_low}")
print(f"  swing_high_idx={swing_high_idx} ({date_of(swing_high_idx)}) val={swing_high_val}")
print(f"  swing_low_idx={swing_low_idx} ({date_of(swing_low_idx)}) val={swing_low_val}")

for i in range(start_i, len(df)):
    ds = date_of(i)
    if ds > '2026-08-05':
        break
    curr_open = opens[i]; curr_high = highs[i]; curr_low = lows[i]
    print(f"\n--- {ds} O={curr_open} H={curr_high} L={curr_low} ---")
    print(f"  dir={current_dir} ref_h={ref_high} ref_l={ref_low}")
    print(f"  sh={date_of(swing_high_idx)}({swing_high_val}) sl={date_of(swing_low_idx)}({swing_low_val})")
    
    obh = curr_open > ref_high; obl = curr_open < ref_low
    bh = (curr_high > ref_high) or obh; bl = (curr_low < ref_low) or obl
    print(f"  obh={obh} obl={obl} bh={bh} bl={bl}")
    
    if not (bh or bl):
        print(f"  INSIDE BAR - skip")
        continue
    
    if bh and bl:
        tf = 0
        if obh: tf = 1; print(f"  OUTSIDE: open > ref_high => HIGH first")
        elif obl: tf = -1; print(f"  OUTSIDE: open < ref_low => LOW first")
        else:
            dh = abs(curr_open - ref_high); dl = abs(curr_open - ref_low)
            tf = -1 if dl < dh else 1
            print(f"  OUTSIDE: dist_h={dh:.2f} dist_l={dl:.2f} => {'LOW' if tf==-1 else 'HIGH'} first")
        
        if tf == 1:
            print(f"  -> process_up_break then process_down_break")
            # up
            if current_dir == -1:
                print(f"     UP: dir=DOWN => CONFIRM SWING LOW at {date_of(swing_low_idx)} val={swing_low_val}")
                print(f"     UP: dir->UP, new sh={ds}({curr_high})")
                current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
            elif current_dir == 1:
                if curr_high >= swing_high_val:
                    print(f"     UP: dir=UP, update sh {swing_high_val}->{curr_high}")
                    swing_high_idx = i; swing_high_val = curr_high
                else:
                    print(f"     UP: dir=UP, h={curr_high} < sh={swing_high_val}, NO CHANGE")
            else:
                print(f"     UP: dir=NEUTRAL => set UP")
                current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
            # down
            if current_dir == 1:
                print(f"     DOWN: dir=UP => CONFIRM SWING HIGH at {date_of(swing_high_idx)} val={swing_high_val}")
                print(f"     DOWN: dir->DOWN, new sl={ds}({curr_low})")
                current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
            elif current_dir == -1:
                if curr_low <= swing_low_val:
                    print(f"     DOWN: dir=DOWN, update sl {swing_low_val}->{curr_low}")
                    swing_low_idx = i; swing_low_val = curr_low
                else:
                    print(f"     DOWN: dir=DOWN, l={curr_low} > sl={swing_low_val}, NO CHANGE")
            else:
                print(f"     DOWN: dir=NEUTRAL => set DOWN")
                current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
        else:
            print(f"  -> process_down_break then process_up_break")
            # down
            if current_dir == 1:
                print(f"     DOWN: dir=UP => CONFIRM SWING HIGH at {date_of(swing_high_idx)} val={swing_high_val}")
                current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
            elif current_dir == -1:
                if curr_low <= swing_low_val:
                    swing_low_idx = i; swing_low_val = curr_low
            else:
                current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
            # up
            if current_dir == -1:
                print(f"     UP: dir=DOWN => CONFIRM SWING LOW at {date_of(swing_low_idx)} val={swing_low_val}")
                current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
            elif current_dir == 1:
                if curr_high >= swing_high_val:
                    swing_high_idx = i; swing_high_val = curr_high
            else:
                current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
    else:
        if current_dir == 1:
            if bl:
                print(f"  DOWN_BREAK: dir=UP => CONFIRM SH at {date_of(swing_high_idx)}({swing_high_val})")
                current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
            elif bh:
                if curr_high >= swing_high_val:
                    print(f"  UP_CONT: update sh->{curr_high}")
                    swing_high_idx = i; swing_high_val = curr_high
        elif current_dir == -1:
            if bh:
                print(f"  UP_BREAK: dir=DOWN => CONFIRM SL at {date_of(swing_low_idx)}({swing_low_val})")
                current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
            elif bl:
                if curr_low <= swing_low_val:
                    print(f"  DOWN_CONT: update sl->{curr_low}")
                    swing_low_idx = i; swing_low_val = curr_low
        else:
            if bh: current_dir = 1; swing_high_idx = i; swing_high_val = curr_high
            elif bl: current_dir = -1; swing_low_idx = i; swing_low_val = curr_low
    
    ref_high = curr_high; ref_low = curr_low
    print(f"  END: dir={current_dir} sh={date_of(swing_high_idx)}({swing_high_val}) sl={date_of(swing_low_idx)}({swing_low_val})")
