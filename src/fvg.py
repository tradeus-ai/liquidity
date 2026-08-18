import pandas as pd
import logging

logger = logging.getLogger('fvg')

def identify_fvgs(df, limit=150):
    """
    Scans the OHLC dataframe and identifies unmitigated Fair Value Gaps (FVGs).
    FVG is formed using structural bars (ignoring inside bars), 
    where a gap exists between the bar two structural steps ago and the current bar.
    """
    if len(df) < 3:
        return []
        
    active_fvgs = []
    
    ref_high = df['high'].iloc[0]
    ref_low = df['low'].iloc[0]
    ref_date = df.index[0]
    
    ref1_high = None
    ref1_low = None
    ref1_date = None
    
    ref2_high = ref_high
    ref2_low = ref_low
    ref2_date = ref_date
    
    for i in range(1, len(df)):
        date = df.index[i]
        curr_high = float(df['high'].iloc[i])
        curr_low = float(df['low'].iloc[i])
        curr_open = float(df['open'].iloc[i])
        
        # Determine if current bar breaks previous structural reference
        open_broke_high = curr_open > ref_high
        open_broke_low = curr_open < ref_low
        
        broke_high = curr_high > ref_high or open_broke_high
        broke_low = curr_low < ref_low or open_broke_low
        
        if broke_high or broke_low:
            # Shift references: ref2 -> ref1, current -> ref
            ref1_high = ref2_high
            ref1_low = ref2_low
            ref1_date = ref2_date
            
            ref2_high = ref_high
            ref2_low = ref_low
            ref2_date = ref_date
            
            ref_high = curr_high
            ref_low = curr_low
            ref_date = date
            
            # Check for new FVGs if we have enough structural history
            if ref1_date is not None:
                # Bullish FVG: current low is higher than ref1 high
                if curr_low > ref1_high:
                    active_fvgs.append({
                        'type': 'bull',
                        'start_time': ref1_date,
                        'top': curr_low,
                        'bottom': ref1_high
                    })
                
                # Bearish FVG: current high is lower than ref1 low
                if curr_high < ref1_low:
                    active_fvgs.append({
                        'type': 'bear',
                        'start_time': ref1_date,
                        'top': ref1_low,
                        'bottom': curr_high
                    })
                    
        # FVG Mitigation (runs on every bar, not just structural ones)
        if active_fvgs:
            unmitigated = []
            for fvg in active_fvgs:
                is_mitigated = False
                if fvg['type'] == 'bull':
                    # Bullish FVG is fully mitigated if price dips below its bottom
                    if curr_low <= fvg['bottom']:
                        is_mitigated = True
                elif fvg['type'] == 'bear':
                    # Bearish FVG is fully mitigated if price rises above its top
                    if curr_high >= fvg['top']:
                        is_mitigated = True
                
                if not is_mitigated:
                    unmitigated.append(fvg)
                    
            active_fvgs = unmitigated
            
        # Keep only the most recent N FVGs to prevent frontend clutter
        if len(active_fvgs) > limit:
            active_fvgs = active_fvgs[-limit:]
            
    # Set the end_time for the UI rendering (extends to the rightmost edge of the chart)
    last_date = df.index[-1]
    for fvg in active_fvgs:
        fvg['end_time'] = last_date
        
    logger.info(f"Identified {len(active_fvgs)} active/unmitigated FVGs.")
    return active_fvgs
