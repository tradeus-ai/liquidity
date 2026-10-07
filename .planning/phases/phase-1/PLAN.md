# Phase 1 Plan: Trading Alert System

## Overview
Implement the trading alert system based on the provided Design Document.

## Objectives
- Scaffold the modular Python architecture (`data_fetcher.py`, `strategy_engine.py`, `alert_manager.py`, `main.py`).
- Fetch concurrent OHLCV data for symbols in `Futures.csv` using TradingView data feed (e.g., `tvDatafeed`).
- Process data using `smartmoneyconcepts` to identify liquidity sweeps, order blocks, and FVG conditions.
- Trigger buy/sell alerts and send them to Telegram with resilient SQLite-backed retry logic.
- Reuse existing OCI Terraform setup for deployment.

## Step-by-Step Implementation

### Step 1: Initialize Project & Scaffold Architecture
- Create Python virtual environment and `requirements.txt` with dependencies (`pandas`, `tvDatafeed`, `smartmoneyconcepts`, `telethon` or `python-telegram-bot`, `sqlite3`).
- Create empty module files: `data_fetcher.py`, `strategy_engine.py`, `alert_manager.py`, and `main.py`.

### Step 2: Implement Data Fetcher (`data_fetcher.py`)
- Read `Futures.csv` to get the list of symbols.
- Use `tvDatafeed` (or an equivalent) to fetch Daily (HTF) and 15m/1h (LTF) historical data.
- Implement concurrent fetching using `asyncio` or `ThreadPoolExecutor`.
- Return cleaned pandas DataFrames.

### Step 3: Implement Strategy Engine (`strategy_engine.py`)
- Integrate `smartmoneyconcepts` to calculate pullbacks, swing highs/lows, BOS, ChoCH, Order Blocks, and FVGs.
- Map custom entry logic:
  - Check for Liquidity Sweeps, OB reactions, and FVG reactions (without inside bars).
  - Check Execution triggers (closing inside recent bullish/bearish FVGs).
  - Calculate Stop Loss and Targets based on SMC pullbacks.

### Step 4: Implement Alert Manager (`alert_manager.py`)
- Set up SQLite database to store pending alerts.
- Integrate Telegram Bot API.
- Create a worker loop that attempts to send alerts from the DB, applying exponential backoff on failures.

### Step 5: Implement Main Controller (`main.py`)
- Initialize the SQLite database.
- Start the Telegram alert worker thread/task.
- Create the main continuous monitoring loop:
  - Fetch data for all symbols.
  - Run the Strategy Engine.
  - If conditions are met, queue an alert via the Alert Manager.
  - Sleep for the required interval (e.g., 15 minutes).

### Step 6: Verify Infrastructure Re-use
- Ensure `infrastructure/main.tf` can be used to deploy the final script.
- Document the manual deployment steps (SSH + git pull) in a `deploy_runbook.md` or similar file.

## Verification
- Unit test data fetching logic (mock API responses).
- Test strategy engine with historical OHLCV data to confirm trade entries match expected behavior.
- Test Telegram alert delivery and the SQLite retry queue (simulate network failure).
- Ensure the main loop runs continuously without blocking.
