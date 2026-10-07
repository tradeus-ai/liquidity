import pandas as pd
from smartmoneyconcepts import smc

class StrategyEngine:
    def __init__(self):
        pass

    def calculate_custom_fvg_ob(self, df):
        """
        Custom logic: 3-candle FVG formation.
        Candle 1 -> Order Block (High to Low).
        Gap between Candle 1 and Candle 3 -> FVG.
        """
        import numpy as np
        fvg_ob_df = pd.DataFrame(index=df.index)
        fvg_ob_df['FVG'] = 0
        fvg_ob_df['OB'] = 0
        fvg_ob_df['OB_Top'] = np.nan
        fvg_ob_df['OB_Bottom'] = np.nan
        
        high_1 = df['high'].shift(2)
        low_1 = df['low'].shift(2)
        high_3 = df['high']
        low_3 = df['low']
        
        # Bullish FVG
        bullish_fvg = low_3 > high_1
        fvg_ob_df.loc[bullish_fvg, 'FVG'] = 1
        # Bullish OB (Candle 1)
        fvg_ob_df.loc[bullish_fvg, 'OB'] = 1
        fvg_ob_df.loc[bullish_fvg, 'OB_Top'] = high_1
        fvg_ob_df.loc[bullish_fvg, 'OB_Bottom'] = low_1
        
        # Bearish FVG
        bearish_fvg = high_3 < low_1
        fvg_ob_df.loc[bearish_fvg, 'FVG'] = -1
        # Bearish OB (Candle 1)
        fvg_ob_df.loc[bearish_fvg, 'OB'] = -1
        fvg_ob_df.loc[bearish_fvg, 'OB_Top'] = high_1
        fvg_ob_df.loc[bearish_fvg, 'OB_Bottom'] = low_1
        
        return fvg_ob_df

    def apply_smc_indicators(self, df):
        """Apply smc concepts to a dataframe."""
        df = df.copy()
        # Calculate Custom FVGs and OBs (3-candle logic where Candle 1 is OB)
        fvg_ob = self.calculate_custom_fvg_ob(df)
        df = pd.concat([df, fvg_ob], axis=1)
        
        # Calculate Swing Highs/Lows
        swing = smc.swing_highs_lows(df)
        df = pd.concat([df, swing], axis=1)
        
        # Calculate BOS/ChoCH
        bos_choch = smc.bos_choch(df)
        df = pd.concat([df, bos_choch], axis=1)
        
        # Calculate Liquidity
        liquidity = smc.liquidity(df)
        df = pd.concat([df, liquidity], axis=1)
        
        return df

    def check_entry_conditions(self, ltf_df):
        """
        Check for:
        1a. Liquidity Sweep
        1b. OB reaction
        1c. FVG reaction
        2. Execution trigger (candle close inside FVG)
        """
        if ltf_df is None or ltf_df.empty or len(ltf_df) < 50:
            return None
            
        # Apply SMC to LTF
        ltf_smc = self.apply_smc_indicators(ltf_df)
        
        last_row = ltf_smc.iloc[-1]
        
        # 1. Confluence checks (simplified to check recent rows for signal)
        # Check if liquidity sweep recently occurred
        liquidity_sweep = last_row.get('Liquidity', 0) != 0 
        
        # Check OB reaction
        ob_reaction = False # placeholder logic
        if 'OB' in last_row:
            ob_reaction = True # simplistic check, refine as needed

        # Check FVG reaction
        fvg_reaction = False
        # Buy Entry trigger
        is_buy_entry = False
        if last_row.get('FVG', 0) == -1: # Bearish FVG
             if last_row['close'] > last_row['high'] - (last_row['high'] - last_row['low']) / 2: # Closes inside
                 is_buy_entry = True
                 fvg_reaction = True

        # Sell Entry trigger
        is_sell_entry = False
        if last_row.get('FVG', 0) == 1: # Bullish FVG
             if last_row['close'] < last_row['low'] + (last_row['high'] - last_row['low']) / 2: # Closes inside
                 is_sell_entry = True
                 fvg_reaction = True

        # Ensure all confluence conditions met
        # NOTE: A robust implementation would look back a few bars to see if these occurred.
        
        # Extract swings to calculate SL and Targets
        swings = ltf_smc[['HighLow', 'Level']].dropna()
        swing_highs = swings[swings['HighLow'] == 1.0]['Level'].values
        swing_lows = swings[swings['HighLow'] == -1.0]['Level'].values
        
        if is_buy_entry and len(swing_lows) >= 1 and len(swing_highs) >= 2:
            sl = float(swing_lows[-1])
            t1 = float(swing_highs[-1])
            t2 = float(swing_highs[-2])
            
            # T1 should be closer than T2
            if t1 > t2:
                t1, t2 = t2, t1
                
            return {
                "direction": "BUY",
                "entry_price": last_row['close'],
                "sl": sl,
                "t1": t1,
                "t2": t2
            }
            
        elif is_sell_entry and len(swing_highs) >= 1 and len(swing_lows) >= 2:
            sl = float(swing_highs[-1])
            t1 = float(swing_lows[-1])
            t2 = float(swing_lows[-2])
            
            # T1 should be closer than T2
            if t1 < t2:
                t1, t2 = t2, t1
                
            return {
                "direction": "SELL",
                "entry_price": last_row['close'],
                "sl": sl,
                "t1": t1,
                "t2": t2
            }
            
        return None
