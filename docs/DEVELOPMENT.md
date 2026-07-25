# Development

## Local Setup
1. Ensure Python 3.8+ is installed.
2. Clone the repository.
3. Create a virtual environment: `python -m venv .venv`
4. Activate: `source .venv/bin/activate`
5. Install dependencies: `pip install pandas numpy tvDatafeed pyarrow lightweight-charts`

## Commands

| Command | Description |
|---|---|
| `python app.py` | Start the web dashboard at `http://127.0.0.1:8080` |
| `python main.py` | Generate static `chart_1d.html` and `chart_15m.html` with all SMC overlays |
| `python test_fetch.py` | Verify TradingView API connectivity |

## Web Dashboard Features
- **Multi-Symbol Dropdown**: 215+ NSE Futures symbols loaded from `Futures.csv`
- **Timeframe Switching**: 1D, 1H, 15m, 5m — instant switch via topbar buttons
- **SMC Overlays**: Pullbacks, Inducement (#), Inducement Shift (IS), BOS, ChoCH
- **Master Toggle**: Single checkbox to show/hide all SMC structure overlays
- **Individual Toggles**: Fine-tune visibility of each overlay type
- **Interactive Toolbox**: Draw lines, boxes, and annotations directly on the chart
- **Correction Feedback**: Submit chart corrections via the feedback panel

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Render the interactive dashboard |
| `/api/data?symbol=X&timeframe=Y` | GET | Return chart data as JSON (candles, pullback points, HTF events, zones) |
| `/api/symbols` | GET | Return the list of available symbols |
| `/api/feedback` | POST | Save chart correction feedback to `chart_feedback.json` |

## Code Style
Standard PEP-8 conventions are recommended. No enforced linters are currently configured.

## PR Process
1. Create your branch from `main`.
2. Test with `python main.py` (static charts) and `python app.py` (web dashboard).
3. Verify the date scale is visible at the bottom of the chart.
4. Open a pull request describing your changes.
