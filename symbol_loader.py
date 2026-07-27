import pandas as pd
import os

BASE_DIR = os.path.dirname(__file__)

def get_symbol_list(market_type='futures'):
    """
    Parses Futures.csv or NSE_all_stocks.csv based on market_type ('futures' or 'equity')
    and returns a sorted list of unique symbols.
    """
    m_type = str(market_type).lower().strip()
    
    if m_type == 'forex':
        return ['AUDUSD', 'EURUSD', 'USDJPY', 'GBPUSD', 'USDCAD', 'USDCHF', 'NZDUSD']
    if m_type == 'metals':
        return ['XAUUSD', 'XAGUSD']
    
    if m_type == 'equity':
        paths_to_try = [
            os.path.join(BASE_DIR, "stocks list", "NSE_all_stocks.csv"),
            os.path.join(BASE_DIR, "NSE_all_stocks.csv")
        ]
    else:
        paths_to_try = [
            os.path.join(BASE_DIR, "stocks list", "Futures.csv"),
            os.path.join(BASE_DIR, "Futures.csv")
        ]
        
    target_csv = None
    for p in paths_to_try:
        if os.path.exists(p):
            target_csv = p
            break
            
    if not target_csv:
        if m_type == 'equity':
            return ["AMBUJACEM", "CANBK", "RELIANCE", "HDFCBANK", "INFY", "TCS"]
        else:
            return ["AMBUJACEM", "NIFTY", "BANKNIFTY", "RELIANCE", "INFY", "TCS"]
            
    try:
        df = pd.read_csv(target_csv)
        if 'Symbol' in df.columns:
            symbols = df['Symbol'].dropna().astype(str).str.strip().tolist()
            # Remove empty strings
            symbols = [s for s in symbols if s]
            symbols = sorted(list(set(symbols)))
            return symbols
    except Exception as e:
        print(f"Error reading {target_csv}: {e}")
        
    return ["AMBUJACEM", "RELIANCE", "INFY", "TCS"]

if __name__ == "__main__":
    fut = get_symbol_list('futures')
    eq = get_symbol_list('equity')
    print(f"Loaded {len(fut)} futures symbols. First 5:", fut[:5])
    print(f"Loaded {len(eq)} equity symbols. First 5:", eq[:5])
