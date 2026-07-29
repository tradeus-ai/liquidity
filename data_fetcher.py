import os
import pandas as pd
from tvDatafeed import TvDatafeedLive, Interval
from config import TV_USERNAME, TV_PASSWORD

class DataFetcher:
    def __init__(self, data_dir="data"):
        self.tv = TvDatafeedLive(TV_USERNAME, TV_PASSWORD)
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def _get_file_path(self, symbol, interval):
        safe_symbol = symbol.replace('!', '_bang')
        return os.path.join(self.data_dir, f"{safe_symbol}_{interval}.parquet")

    def fetch_data(self, symbol, exchange, interval_enum, interval_name, n_bars_initial=5000, n_bars_update=500):
        """
        Fetches data with caching. If cache exists, fetches the last few candles and merges.
        """
        file_path = self._get_file_path(symbol, interval_name)
        
        if os.path.exists(file_path):
            print(f"[{symbol} {interval_name}] Local cache found. Loading and checking for updates...")
            df_local = pd.read_parquet(file_path)
            
            # Fetch recent data to update
            print(f"[{symbol} {interval_name}] Fetching {n_bars_update} recent candles for update...")
            df_recent = self.tv.get_hist(symbol=symbol, exchange=exchange, interval=interval_enum, n_bars=n_bars_update)
            
            if df_recent is not None and not df_recent.empty:
                # Merge and drop duplicates based on index
                df_combined = pd.concat([df_local, df_recent])
                # Keeping the last occurrence in case recent data updated past candles
                df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
                df_combined = df_combined.sort_index()
                
                # Save updated cache
                df_combined.to_parquet(file_path)
                print(f"[{symbol} {interval_name}] Cache updated. Total rows: {len(df_combined)}")
                return df_combined
            else:
                print(f"[{symbol} {interval_name}] Could not fetch recent data. Using local cache.")
                return df_local
        else:
            print(f"[{symbol} {interval_name}] No local cache found. Fetching {n_bars_initial} candles...")
            df = self.tv.get_hist(symbol=symbol, exchange=exchange, interval=interval_enum, n_bars=n_bars_initial)
            
            if df is not None and not df.empty:
                df.to_parquet(file_path)
                print(f"[{symbol} {interval_name}] Data fetched and saved to cache. Total rows: {len(df)}")
            else:
                print(f"[{symbol} {interval_name}] Failed to fetch data.")
                
            return df
