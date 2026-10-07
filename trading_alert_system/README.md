# Trading Alert System

An automated trading alert system that monitors financial instruments, applies Smart Money Concepts (SMC) to 15-minute timeframe data, and sends entry/exit alerts to a Telegram channel.

## Prerequisites
- Python 3.9+
- A Telegram Bot Token (from BotFather)
- A Telegram Chat ID (where the bot will send messages)

## Local Setup

1. **Navigate to the system directory:**
   ```bash
   cd trading_alert_system
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application:**
   Open `config.py` and update the following values:
   - `TELEGRAM_TOKEN`: Your bot's API token.
   - `TELEGRAM_CHAT_ID`: The chat ID where alerts should be sent.
   - `SYMBOLS_LIST`: Add the symbols you want to track (e.g., `["BANKNIFTY", "NIFTY"]`).
     *Note: If `SYMBOLS_LIST` is empty, it will fall back to reading symbols from `../stocks list/Futures.csv`.*

5. **Run the system:**
   ```bash
   python main.py
   ```

## Architecture

- **`config.py`**: Centralized configuration for API keys, symbol lists, and polling intervals.
- **`data_fetcher.py`**: Concurrently fetches OHLCV 15-minute timeframe data using `tvDatafeed`.
- **`strategy_engine.py`**: Analyzes the price data using the `smartmoneyconcepts` library to detect Order Blocks (OB), Fair Value Gaps (FVG), Liquidity Sweeps, and entry execution triggers.
- **`alert_manager.py`**: Queues alerts in a local SQLite database (`alerts.db`) and asynchronously sends them via Telegram with exponential backoff and retry logic.
- **`main.py`**: The central controller that runs in a continuous monitoring loop, checking entry conditions and triggering the alert manager.

## Deployment
For cloud deployment using Terraform to Oracle Cloud Infrastructure (OCI), refer to [`deploy_runbook.md`](deploy_runbook.md).
