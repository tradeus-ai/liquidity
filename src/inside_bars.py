import pandas as pd
import logging

logger = logging.getLogger('inside_bars')

def identify_inside_bar_zones(df):
    """
    Scans the OHLC dataframe and identifies sequences of inside bars.
    Returns a list of dictionaries representing the inside bar zones (Mother Bar to Last Inside Bar).
    """
    if len(df) < 2:
        return []
        
    zones = []
    
    ref_high = df['high'].iloc[0]
    ref_low = df['low'].iloc[0]
    ref_date = df.index[0]
    
    current_inside_sequence = []
    
    for i in range(1, len(df)):
        date = df.index[i]
        curr_high = df['high'].iloc[i]
        curr_low = df['low'].iloc[i]
        
        broke_high = curr_high > ref_high
        broke_low = curr_low < ref_low
        
        if broke_high or broke_low:
            # Breakout occurred. If we had an active inside sequence, close it and save the zone.
            if len(current_inside_sequence) > 0:
                zones.append({
                    'start_time': ref_date,
                    'end_time': current_inside_sequence[-1],
                    'high': ref_high,
                    'low': ref_low
                })
                current_inside_sequence = []
                
            # Update reference candle to the breakout candle
            ref_high = curr_high
            ref_low = curr_low
            ref_date = date
        else:
            # Inside bar detected!
            current_inside_sequence.append(date)
            
    # Close any sequence at the end of the dataframe
    if len(current_inside_sequence) > 0:
        zones.append({
            'start_time': ref_date,
            'end_time': current_inside_sequence[-1],
            'high': ref_high,
            'low': ref_low
        })
        
    logger.info(f"Identified {len(zones)} inside bar zones.")
    return zones
