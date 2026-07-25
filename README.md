<!-- generated-by: gsd-doc-writer -->
# Liquidity Market Structure Analyzer

A Python tool for analyzing market liquidity structure (Inducements, Break of Structure, Change of Character) across different timeframes to find high-probability trade setups based on market structure changes.

## Features

- **Market Structure Identification**: Automatically identifies swing points, Inducements, BOS, and ChoCH.
- **Zone Marking**: Detects supply and demand zones based on market extremes.
- **Data Fetching**: Fetches financial data using TradingView's API (`tvDatafeed`) with local caching in Parquet format.
- **Visualizations**: Plots candlestick charts with structure events mapped visually using `mplfinance`.

## Installation

This project uses Python. To set it up, create a virtual environment and install the required dependencies (such as `pandas`, `numpy`, `mplfinance`, and `tvDatafeed`).

```bash
# Clone the repository
git clone <repository_url>
cd Liquidity

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`

# Install dependencies
pip install pandas numpy mplfinance tvDatafeed pyarrow
```

## Quick Start

Run the main analysis script. It will fetch the latest market data, identify market structure, and generate chart images.

```bash
python main.py
```
This command generates two charts in the root directory:
- `chart_1d.png` (Daily Timeframe)
- `chart_15m.png` (15-Minute Timeframe)

## Usage Example

The core structure analysis is handled by the `MarketStructureAnalyzer` class:

```python
import pandas as pd
from market_structure import MarketStructureAnalyzer

# Assuming df is a Pandas DataFrame with OHLC data
analyzer = MarketStructureAnalyzer(df)
structured_df = analyzer.identify_structure()

# The resulting dataframe contains columns like 'structure_event' and 'zone_type'
events = structured_df.dropna(subset=['structure_event'])
print(events[['close', 'structure_event']])
```
