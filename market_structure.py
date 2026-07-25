import pandas as pd
import numpy as np
from smc_pullback import find_swings

class MarketStructureAnalyzer:
    def __init__(self, df, timeframe=None, ltf_df=None):
        self.df = df.copy()
        self.timeframe = timeframe
        self.ltf_df = ltf_df

    def find_swing_points(self):
        """Delegate swing detection to the smc_pullback module."""
        self.df = find_swings(self.df, ltf_df=self.ltf_df)
        return self.df

    def identify_structure(self):
        """
        Identify Inducement, BOS and ChoCH.
        """
        self.find_swing_points()
        
        # New columns for structure
        self.df['zone_type'] = None # 'DEMAND' or 'SUPPLY'
        self.df['zone_high'] = np.nan
        self.df['zone_low'] = np.nan
        
        trend = 1 # Assume starting in uptrend
        market_high = None
        market_low = None
        
        last_swing_high = None
        last_swing_high_idx = None
        last_swing_low = None
        last_swing_low_idx = None
        
        highest_since_struct = None
        lowest_since_struct = None
        
        market_high_idx = None
        market_low_idx = None
        
        # To keep track of the candle that formed the extreme
        extreme_high_idx = None
        extreme_low_idx = None

        for i in range(1, len(self.df)):
            idx = self.df.index[i]
            row = self.df.iloc[i]
            
            if row['is_swing_high']: 
                last_swing_high = row['high']
                last_swing_high_idx = idx
            if row['is_swing_low']: 
                last_swing_low = row['low']
                last_swing_low_idx = idx
            
            # Keep track of absolute extremes and their indices
            if highest_since_struct is None or row['high'] > highest_since_struct: 
                highest_since_struct = row['high']
                extreme_high_idx = idx
            if lowest_since_struct is None or row['low'] < lowest_since_struct: 
                lowest_since_struct = row['low']
                extreme_low_idx = idx
            
            if trend == 1:
                # 1. Inducement Check
                if market_high is None and last_swing_low is not None:
                    if row['low'] < last_swing_low:
                        market_high = highest_since_struct
                        market_high_idx = extreme_high_idx
                        self.df.loc[idx, 'structure_event'] = 'INDUCEMENT_TAKEN_UP'
                        self.df.loc[idx, 'market_high'] = market_high
                        self.df.loc[idx, 'event_start_idx'] = last_swing_low_idx
                        self.df.loc[idx, 'event_start_val'] = last_swing_low
                        self.df.loc[idx, 'event_end_idx'] = idx
                        self.df.loc[idx, 'event_end_val'] = last_swing_low
                
                # 2. ChoCH Check
                if market_low is not None and row['low'] < market_low:
                    self.df.loc[idx, 'structure_event'] = 'CHOCH_DOWN'
                    self.df.loc[idx, 'event_start_idx'] = market_low_idx
                    self.df.loc[idx, 'event_start_val'] = market_low
                    self.df.loc[idx, 'event_end_idx'] = idx
                    self.df.loc[idx, 'event_end_val'] = market_low
                    trend = -1
                    market_high = None
                    market_low = None
                    highest_since_struct = row['high']
                    lowest_since_struct = row['low']
                    extreme_high_idx = idx
                    extreme_low_idx = idx
                    continue
                    
                # 3. BOS Check
                if market_high is not None and row['close'] > market_high:
                    self.df.loc[idx, 'structure_event'] = 'BOS_UP'
                    self.df.loc[idx, 'event_start_idx'] = market_high_idx
                    self.df.loc[idx, 'event_start_val'] = market_high
                    self.df.loc[idx, 'event_end_idx'] = idx
                    self.df.loc[idx, 'event_end_val'] = market_high
                    market_low = lowest_since_struct
                    market_low_idx = extreme_low_idx
                    
                    # Mark the Demand Zone at the extreme low before the BOS
                    if extreme_low_idx is not None:
                        self.df.loc[extreme_low_idx, 'zone_type'] = 'DEMAND'
                        # A simple way to mark zone is the full candle of the extreme low
                        self.df.loc[extreme_low_idx, 'zone_high'] = self.df.loc[extreme_low_idx, 'high']
                        self.df.loc[extreme_low_idx, 'zone_low'] = self.df.loc[extreme_low_idx, 'low']
                        
                    market_high = None
                    highest_since_struct = row['high']
                    lowest_since_struct = row['low']
                    extreme_high_idx = idx
                    extreme_low_idx = idx
                    
            elif trend == -1:
                # 1. Inducement Check
                if market_low is None and last_swing_high is not None:
                    if row['high'] > last_swing_high:
                        market_low = lowest_since_struct
                        market_low_idx = extreme_low_idx
                        self.df.loc[idx, 'structure_event'] = 'INDUCEMENT_TAKEN_DOWN'
                        self.df.loc[idx, 'market_low'] = market_low
                        self.df.loc[idx, 'event_start_idx'] = last_swing_high_idx
                        self.df.loc[idx, 'event_start_val'] = last_swing_high
                        self.df.loc[idx, 'event_end_idx'] = idx
                        self.df.loc[idx, 'event_end_val'] = last_swing_high
                
                # 2. ChoCH Check
                if market_high is not None and row['high'] > market_high:
                    self.df.loc[idx, 'structure_event'] = 'CHOCH_UP'
                    self.df.loc[idx, 'event_start_idx'] = market_high_idx
                    self.df.loc[idx, 'event_start_val'] = market_high
                    self.df.loc[idx, 'event_end_idx'] = idx
                    self.df.loc[idx, 'event_end_val'] = market_high
                    trend = 1
                    market_high = None
                    market_low = None
                    highest_since_struct = row['high']
                    lowest_since_struct = row['low']
                    extreme_high_idx = idx
                    extreme_low_idx = idx
                    continue
                    
                # 3. BOS Check
                if market_low is not None and row['close'] < market_low:
                    self.df.loc[idx, 'structure_event'] = 'BOS_DOWN'
                    self.df.loc[idx, 'event_start_idx'] = market_low_idx
                    self.df.loc[idx, 'event_start_val'] = market_low
                    self.df.loc[idx, 'event_end_idx'] = idx
                    self.df.loc[idx, 'event_end_val'] = market_low
                    market_high = highest_since_struct
                    market_high_idx = extreme_high_idx
                    
                    # Mark the Supply Zone at the extreme high before the BOS
                    if extreme_high_idx is not None:
                        self.df.loc[extreme_high_idx, 'zone_type'] = 'SUPPLY'
                        self.df.loc[extreme_high_idx, 'zone_high'] = self.df.loc[extreme_high_idx, 'high']
                        self.df.loc[extreme_high_idx, 'zone_low'] = self.df.loc[extreme_high_idx, 'low']
                        
                    market_low = None
                    highest_since_struct = row['high']
                    lowest_since_struct = row['low']
                    extreme_high_idx = idx
                    extreme_low_idx = idx

        return self.df
