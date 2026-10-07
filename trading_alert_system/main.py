import asyncio
import time
import pandas as pd
from data_fetcher import DataFetcher
from strategy_engine import StrategyEngine
from alert_manager import AlertManager
from trade_manager import TradeManager
import config

async def main():
    print("Initializing Trading Alert System...")
    # 1. Initialize components
    fetcher = DataFetcher()
    engine = StrategyEngine()
    trade_mgr = TradeManager()
    
    alert_mgr = AlertManager(
        telegram_token=config.TELEGRAM_TOKEN,
        chat_id=config.TELEGRAM_CHAT_ID
    )

    # 2. Start the alert manager background task
    asyncio.create_task(alert_mgr.worker_loop())

    # Send summary of stats at start
    stats = trade_mgr.get_stats_summary()
    print(stats)
    alert_mgr.queue_alert("SYSTEM", stats)

    # 3. Main monitoring loop
    while True:
        try:
            print("Starting data fetch cycle...")
            # Load symbols
            if config.SYMBOLS_LIST:
                df = pd.DataFrame({'Symbol': config.SYMBOLS_LIST})
            else:
                df = pd.read_csv(config.SYMBOLS_CSV_PATH)
            
            # Fetch data (concurrently)
            data_results = await fetcher.fetch_all_symbols(df)
            
            # Analyze & Alert
            for symbol, ltf_df in data_results:
                if ltf_df is not None and not ltf_df.empty:
                    last_row = ltf_df.iloc[-1]
                    current_high = last_row['high']
                    current_low = last_row['low']
                    current_close = last_row['close']
                    
                    # 1. Evaluate open trades for targets/SL
                    trade_mgr.check_and_update_trades(
                        symbol, current_high, current_low, current_close, alert_mgr
                    )
                    
                    # 2. Check for new entries if no trade is active
                    if not trade_mgr.has_active_trade(symbol):
                        signal = engine.check_entry_conditions(ltf_df)
                        if signal:
                            trade_mgr.open_trade(
                                symbol, 
                                signal['direction'], 
                                signal['entry_price'], 
                                signal['sl'], 
                                signal['t1'], 
                                signal['t2'], 
                                alert_mgr
                            )
            
            # Sleep based on config
            sleep_time = config.POLL_INTERVAL_SECONDS
            print(f"Cycle complete. Sleeping for {sleep_time // 60} minutes.")
            await asyncio.sleep(sleep_time)
        except Exception as e:
            print(f"Error in main loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
