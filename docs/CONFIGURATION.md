<!-- generated-by: gsd-doc-writer -->
# Configuration

## Environment Variables
This project does not require any environment variables to run.

## Config File Format
There are no external configuration files (JSON, YAML, etc.) required. 

## Required vs Optional Settings
The application currently configures target assets directly within the `main.py` script.

To change the asset being analyzed, modify the following variables in `main.py`:
- **`symbol`**: The TradingView symbol string (e.g., `'AMBUJACEM1!'`)
- **`exchange`**: The exchange on which the symbol trades (e.g., `'NSE'`)

## Defaults
- The `DataFetcher` class defaults to caching data in a local `data/` directory.
- For updating the cache, it fetches `500` recent bars by default.
- For the initial full fetch, it requests `5000` bars.
- The chart visualizations plot the most recent `300` candles by default.
