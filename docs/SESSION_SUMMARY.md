# Liquidity Dashboard — Full Session Summary

**Date**: 25 July 2026  
**Project**: `/mnt/all/Trading/Courses/Xoduse/Liquidity`  
**Stack**: Python, lightweight-charts, tvDatafeed, HTML/JS, HTTP server

---

## Overview

This document summarises all work done to build and enhance the **Liquidity Market Structure Dashboard** — an interactive web app for analysing NSE Futures charts using Smart Money Concepts (SMC).

---

## 1. Pullback Logic Enhancements

### Problem: Open of candle can break prev high/low
When a candle opens outside the previous candle's range, the open itself constitutes a break of the high or low. This must be detected before scanning candle H/L.

**Fix in `smc_pullback.py`**:
- Added **open gap break** check: if `open > prev_high` → HIGH taken first at open; if `open < prev_low` → LOW taken first at open
- Added **open proximity** check for outside bars: compare `|curr_open - prev_high|` vs `|curr_open - prev_low|` to determine which level is nearer and therefore broken first

```python
dist_high = abs(curr_open - prev_high)
dist_low  = abs(curr_open - prev_low)
# Whichever distance is smaller → that level is taken first
```

---

## 2. Date Scale & Layout Fixes

### Problem: Date scale not visible on the chart
The chart was rendering at 100vh while the topbar took up 50px, clipping the bottom date axis below the viewport.

**Fix**:
```css
/* Constrain chart to remaining height after header */
.handler, #container {
    height: calc(100vh - 50px) !important;
}
body {
    padding-top: 50px !important;  /* Push chart below fixed header */
}
```

### Problem: Topbar (symbol selector) appeared at the bottom (footer)
Root cause: `web_dashboard.py` injects the topbar HTML **after** the chart HTML in the DOM, so it rendered at the bottom as a footer.

**Fix**: Changed `.custom-topbar` to `position: fixed; top: 0` so it always pins to the top of the viewport regardless of DOM position.

```css
.custom-topbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 50px;
    z-index: 9999;
}
```

---

## 3. Structure Caching Engine

### Problem: Pullback and market structure was recalculated for every request (slow)

**Solution**: Created `structure_service.py` — a persistent JSON caching layer.

- **Cache location**: `data/structure_cache/{symbol}_{timeframe}.json`
- **Cache validation**: Compares `last_timestamp` and `total_candles` against live data
- **Cache hit**: Returns computed structure in **< 10ms**
- **Cache miss**: Full recomputation (2-5 seconds), then saves to disk

```bash
# Force recomputation by clearing cache
rm -f data/structure_cache/*.json
```

---

## 4. BOS, ChoCH & Inducement Module

### Created `bos_choch_inducement.py` — HTF State Machine

Implements SMC structure detection for the **Daily (1D)** timeframe:

| Event | Label | Rule |
|---|---|---|
| Inducement | `#` | First pullback low broken in uptrend (or pullback high in downtrend) |
| Inducement Shift | `IS` | Inducement that occurs after a wick break (proper high wicked but not closed above) |
| Break of Structure | `BOS` | Candle **CLOSES** above proper high (uptrend) or below proper low (downtrend) |
| Change of Character | `ChoCH` | Lowest point between BOS start/end breaks — trend flips |

**Key rules**:
- BOS requires a candle **close**, not just a wick
- If a wick breaks proper high without closing → tracked as `wick_high_val`, next inducement becomes IS
- After ChoCH, `current_trend` flips and the cycle restarts

### Chart Lines Drawn
- **Inducement (#)**: Horizontal dashed line from pullback low → candle that broke it, labelled `#`
- **Inducement Shift (IS)**: Same, labelled `IS`
- **BOS**: Line from proper high → candle that closed above, labelled `BOS`
- **ChoCH**: Line from the low between BOS events, labelled `ChoCH`

---

## 5. Web Dashboard (Interactive)

### `app.py` — HTTP Server
Routes:
- `GET /` — Render interactive dashboard via `web_dashboard.py`
- `GET /api/data?symbol=X&timeframe=Y` — JSON payload (candles, pullback, HTF events, zones)
- `GET /api/symbols` — List of 215+ NSE Futures symbols
- `POST /api/feedback` — Save chart corrections to `chart_feedback.json`

### `web_dashboard.py` — Chart Renderer
Uses `lightweight-charts` Python library (`StaticLWC`). Renders:
- White candlesticks (up and down both white)
- Orange pullback line (`#ff9800`, width 3)
- HTF structure markers (Inducement, IS, BOS, ChoCH) — only on 1D
- Demand/Supply zones (green/red boxes) — only on 1D
- Inside bar zones (pink boxes) — all timeframes

### `dashboard.html` — Standalone SPA
Client-side dashboard using `fetch()` to `/api/data`. Supports instant symbol/timeframe switching without page reload.

---

## 6. Layer Toggle Controls

Added to the topbar:

| Toggle | Color | Description |
|---|---|---|
| Master SMC Structure | Green | Turns all overlays ON/OFF simultaneously |
| Pullbacks | Orange `#ff9800` | Orange zigzag pullback line |
| # (IDM) | Yellow `#ffd600` | Inducement marker |
| IS | Cyan `#00e5ff` | Inducement Shift marker |
| BOS | Blue `#2962ff` | Break of Structure marker |
| ChoCH | Magenta `#e91e63` | Change of Character marker |

**Master toggle JS pattern**:
```javascript
function toggleMaster(isChecked) {
    document.querySelectorAll('.layer-toggle').forEach(cb => {
        cb.checked = isChecked;
    });
    toggleLayers();
}
```

---

## 7. Color Disambiguation Fix

**Problem**: IS (Inducement Shift) was orange (`#ff6d00`), which visually overlapped with the orange Pullback line — impossible to distinguish.

**Fix**: Changed IS to Cyan (`#00e5ff`), and Inducement (#) to Bright Yellow (`#ffd600`).

**Final color palette**:
```
Pullback Line     →  #ff9800  (Orange)
Inducement (#)    →  #ffd600  (Yellow)
IS                →  #00e5ff  (Cyan)
BOS               →  #2962ff  (Blue)
ChoCH             →  #e91e63  (Magenta)
```

---

## 8. Files Created / Modified

| File | Status | Purpose |
|---|---|---|
| `smc_pullback.py` | Modified | Open gap break + proximity logic |
| `bos_choch_inducement.py` | **Created** | HTF SMC state machine |
| `structure_service.py` | **Created** | Caching orchestrator |
| `web_dashboard.py` | Modified | Fixed layout: `position:fixed` topbar, `padding-top`, layer toggles |
| `dashboard.html` | Modified | Master toggle, IS cyan color, date scale fixes |
| `app.py` | Modified | Added `/api/data` JSON endpoint |
| `main.py` | Modified | `plot_structure()` now renders HTF events on `chart_1d.html` |
| `docs/ARCHITECTURE.md` | Updated | Current component diagram + module table |
| `docs/DEVELOPMENT.md` | Updated | `python app.py` command + API endpoint docs |
| `docs/LEARNINGS.md` | **Created** | All technical gotchas and patterns |

---

## 9. Market Structure Rules (Reference)

From `GEMINI.md`:
- **Higher Timeframe**: Daily (1D) — for trend and demand/supply zones
- **Lower Timeframe**: 15m (Indian Markets), 1H (Forex) — for entry
- **Data**: NSE Futures from `Futures.csv` via TradingView (`tvDatafeed`)
- **Uptrend BOS**: continues until ChoCH is broken
- **After ChoCH**: previous highest point becomes the new ChoCH level; trend direction is re-evaluated

---

## 10. How to Run

```bash
cd /mnt/all/Trading/Courses/Xoduse/Liquidity
source .venv/bin/activate

# Interactive web dashboard
python app.py
# → Open http://127.0.0.1:8080

# Static chart (chart_1d.html)
python main.py

# Force cache refresh
rm -f data/structure_cache/*.json && python app.py
```
