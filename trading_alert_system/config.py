# Configuration for Trading Alert System

# Telegram Settings
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"

# Data Fetching Settings
# Either use a hardcoded list of symbols or load from CSV. 
# If SYMBOLS_LIST is empty, it will fall back to reading from SYMBOLS_CSV_PATH.
SYMBOLS_LIST = [
    # "BANKNIFTY",
    # "NIFTY",
]

SYMBOLS_CSV_PATH = "../stocks list/Futures.csv"

# Timeframe Settings
# The system now uses 15-minute intervals only.
INTERVAL = "15m"
POLL_INTERVAL_SECONDS = 15 * 60
