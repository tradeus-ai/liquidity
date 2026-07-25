<!-- generated-by: gsd-doc-writer -->
# Getting Started

## Prerequisites
- `Python >= 3.8`

## Installation Steps
1. Clone the repository and navigate into the directory:
```bash
git clone <repository_url>
cd Liquidity
```
2. Create and activate a Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
```
3. Install the required Python packages:
```bash
pip install pandas numpy mplfinance tvDatafeed pyarrow
```

## First Run
Run the main script to fetch data and generate charts:
```bash
python main.py
```
This will fetch OHLC data for the default symbol, run the market structure analysis, and output two PNG files (`chart_1d.png` and `chart_15m.png`) in the root directory.

## Common Setup Issues
- **`ModuleNotFoundError: No module named 'pyarrow'`**: Ensure you install `pyarrow` or `fastparquet` as Pandas requires one of them to read and write the `.parquet` cache files in the `data/` directory.
- **TVDatafeed Authentication Warning**: When running `tvDatafeed()` without credentials, it defaults to a nologin method, which limits the amount of historical data you can access. This is expected and typically sufficient for this project.

## Next Steps
- See [DEVELOPMENT.md](DEVELOPMENT.md) for how to customize the analysis or modify the charts.
- See [TESTING.md](TESTING.md) for instructions on running the test scripts.
