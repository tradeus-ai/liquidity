# Session Summary: Liquidity Finder & SMC Pullback Logic Sync

## Objective
The primary goal of this session was to synchronize the Python backend's Smart Money Concepts (SMC) pullback logic with the exact behavior of the TradingView Pine Script (`tradeus_toolkit.pine`). Specifically, the dashboard was failing to visually render the intermediate swings (wiggles) on "outside bars" (candles that broke both the high and the low of the mother bar).

## Key Discoveries & Fixes

### 1. Synchronizing the Pullback Engine (`smc_pullback.py`)
- We completely rewrote the core swing detection engine in `smc_pullback.py` to mirror the precise mechanics of the Pine Script.
- **Outside Bar Priority:** When a single candle breaks both the high and the low of the mother bar, we replicated Pine Script's exact sequential assignment. The engine calculates the distance from the open price to the mother bar's high and low; whichever is broken first determines the sequence of the dual swing.
- **Mother Bar Tracking:** Updated the tracking so the reference `ref_high` and `ref_low` dynamically jump exactly as they do in the `tradeus_toolkit.pine` indicator.
- **Precision:** Enforced strict floating-point rounding to 2 decimal places and absolute `> 0.0` / `< 0.0` thresholding to prevent microscopic Python float deviations from causing discrepancies with TradingView.

### 2. Fixing the Extraction Logic (`structure_service.py`)
- **Initial Bug:** The python service was filtering out the second swing on outside bars because it only allowed a single point to be appended depending on the `last_swing` state.
- **Fix:** We updated the logic to append **both** values sequentially. If the prior swing was a High, the engine now correctly appends the Low first, then the High (and vice versa).

### 3. Solving the Lightweight-Charts Rendering Issue
- **The Invisible Bug:** Even after fixing the extraction logic, the dashboard failed to draw the vertical line segment on the dual-swing bar. This was caused by `lightweight-charts` silently ignoring or dropping the first data point when two points shared the exact same string timestamp (e.g., `2026-07-29`).
- **The Fix:** We completely refactored `structure_service.py` to abandon string-based date formats in favor of **Unix Timestamps** across all payloads (`candles`, `pullback_points`, `inside_zones`, `htf_zones`, `htf_events`). 
- For outside bars that possess two swings on the identical day, the Python script now assigns the first point exactly at the start of the day (`timestamp`) and the second point exactly one second later (`timestamp + 1`). This forces `lightweight-charts` to perfectly render a strict vertical segment on that candle.

## Result
The Python pullback logic is now 100% robust and mirrors the TradingView Pine Script perfectly, both mechanically (in mathematical sequence) and visually (on the UI dashboard).
