import pandas as pd
import os

FUTURES_CSV = os.path.join(os.path.dirname(__file__), "Futures.csv")

def get_symbol_list():
    """
    Parses Futures.csv and returns a sorted list of unique symbols.
    """
    if not os.path.exists(FUTURES_CSV):
        return ["AMBUJACEM", "NIFTY", "BANKNIFTY", "RELIANCE", "INFY", "TCS"]
        
    try:
        df = pd.read_csv(FUTURES_CSV)
        if 'Symbol' in df.columns:
            symbols = df['Symbol'].dropna().astype(str).str.strip().tolist()
            symbols = sorted(list(set(symbols)))
            return symbols
    except Exception as e:
        print(f"Error reading Futures.csv: {e}")
        
    return ["AMBUJACEM", "NIFTY", "BANKNIFTY", "RELIANCE", "INFY", "TCS"]

if __name__ == "__main__":
    syms = get_symbol_list()
    print(f"Loaded {len(syms)} symbols. First 10:", syms[:10])
