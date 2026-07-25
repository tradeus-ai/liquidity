<!-- generated-by: gsd-doc-writer -->
# Architecture

## System Overview
The Liquidity Market Structure Analyzer is a localized Python script application that retrieves financial market OHLC data, runs a rules-based analysis algorithm to identify key liquidity structures (Inducements, Break of Structure, Change of Character), and visually plots these structures on a candlestick chart.

## Component Diagram
```mermaid
graph TD
    A[main.py (Orchestrator)] --> B[data_fetcher.py (DataFetcher)]
    B --> C[TradingView API (tvDatafeed)]
    B --> D[(Local Parquet Cache)]
    A --> E[market_structure.py (MarketStructureAnalyzer)]
    A --> F[mplfinance (Visualization)]
```

## Data Flow
1. **Initiation**: The orchestrator (`main.py`) requests OHLC data for a specific asset (`AMBUJACEM1!`) across two timeframes (1D, 15m) from the `DataFetcher`.
2. **Data Fetching**: The `DataFetcher` first checks the local `data/` directory for an existing `.parquet` cache. If found, it fetches only the recent required bars from `tvDatafeed` and updates the cache. If not found, it performs a full historical fetch and creates the cache.
3. **Structure Analysis**: The resulting Pandas DataFrame is passed to `MarketStructureAnalyzer`. It iteratively processes the bars to find swing points, validates structural breaks (Inducement, ChoCH, BOS), and assigns these events and their coordinate bounds to new columns.
4. **Plotting**: Finally, `main.py` uses `mplfinance` to render the OHLC data alongside the identified structures (using horizontal and arbitrary lines) and saves the output as PNG images.

## Key Abstractions
- `DataFetcher` (`data_fetcher.py`): Abstracts the TradingView API connection and handles all file-based caching logic.
- `MarketStructureAnalyzer` (`market_structure.py`): Encapsulates the algorithmic logic for interpreting the zigzag structure of the market and appending event data to the DataFrame.

## Directory Structure Rationale
The project uses a flat organizational structure typical of simple data analysis scripts.
```text
.
├── main.py                # Primary entry point
├── market_structure.py    # Core analysis logic
├── data_fetcher.py        # Data access layer
├── data/                  # Local parquet data cache
└── Futures.csv            # Asset symbol references
```
