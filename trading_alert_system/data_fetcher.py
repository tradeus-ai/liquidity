import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import asyncio
from concurrent.futures import ThreadPoolExecutor

class DataFetcher:
    def __init__(self, tv_username=None, tv_password=None):
        # We can initialize tvDatafeed anonymously if we don't need real-time data for some tickers,
        # but for reliable 15m data, a login is often better.
        self.tv = TvDatafeed(tv_username, tv_password)
        self.executor = ThreadPoolExecutor(max_workers=5)
        
    def fetch_symbol_data(self, exchange, symbol):
        """Fetch historical data for a symbol in LTF (15 min) only."""
        try:
            # LTF: 15 min
            ltf_df = self.tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_15_minute, n_bars=500)
            return symbol, ltf_df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return symbol, None

    async def fetch_all_symbols(self, symbols_df, exchange='NSE'):
        """Concurrent fetch for multiple symbols"""
        loop = asyncio.get_running_loop()
        tasks = []
        
        # Third column is Symbol
        for idx, row in symbols_df.iterrows():
            symbol = row['Symbol']
            if pd.isna(symbol):
                continue
            
            task = loop.run_in_executor(
                self.executor,
                self.fetch_symbol_data,
                exchange,
                symbol
            )
            tasks.append(task)
            
        results = await asyncio.gather(*tasks)
        return results

