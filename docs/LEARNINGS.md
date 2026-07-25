# Learnings & Gotchas

Technical patterns, pitfalls, and rules discovered during development.

---

## Lightweight-Charts Layout Rules

### Container Height Constraint
When adding a topbar/header above a `lightweight-charts` chart, the chart container **MUST** use `height: calc(100vh - Xpx)` where `X` = header height. Otherwise the bottom date/time scale axis is clipped below the viewport.

```css
/* ✅ Correct — date scale visible */
.handler, #container {
    height: calc(100vh - 50px) !important;
}

/* ❌ Wrong — date scale clipped */
.handler, #container {
    height: 100vh;
}
```

### DOM Order vs CSS Position
When injecting UI elements after chart HTML (e.g., via `chart._html` from the Python lightweight-charts library), the topbar appears at the **bottom** of the DOM. Use `position: fixed; top: 0` on the header bar and add `body { padding-top: Xpx }` to push the chart content below it.

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
body {
    padding-top: 50px !important;
}
```

### Time Scale Visibility
Always set these chart options to ensure the date axis is visible:
```javascript
timeScale: {
    borderColor: '#363c4e',
    visible: true,
    timeVisible: true,       // shows HH:MM for intraday
    secondsVisible: false,
}
```
- Daily timeframes: display as `YYYY-MM-DD`
- Intraday timeframes: display as `YYYY-MM-DD HH:MM`

---

## SMC Pullback Logic (`smc_pullback.py`)

### Open Gap Breaks
When the current candle's open is **outside** the previous candle's range, the open itself breaks the high or low. This must be checked **before** scanning H/L within the candle body:

```python
# If open > prev_high → HIGH is taken first at open
# If open < prev_low  → LOW is taken first at open
```

### Open Proximity for Outside Bars
When a candle engulfs the previous candle (outside bar), use distance comparison to determine which level is broken first:

```python
dist_high = abs(curr_open - prev_high)
dist_low  = abs(curr_open - prev_low)

if dist_low < dist_high:
    # LOW taken first → previous candle HIGH is a swing high
else:
    # HIGH taken first → previous candle LOW is a swing low
```

---

## SMC Structure: BOS / ChoCH / Inducement (`bos_choch_inducement.py`)

### State Machine Flow
1. **Inducement (#)**: First pullback low broken in uptrend (or pullback high in downtrend)
2. **Inducement Shift (IS)**: Inducement that occurs after a wick break without BOS closure
3. **BOS (Break of Structure)**: Candle **CLOSE** above proper high (uptrend) or below proper low (downtrend) — wick alone is NOT BOS
4. **ChoCH (Change of Character)**: Lowest point between BOS start/end breaks → trend flips

### BOS Requires Candle CLOSE
A wick breaking the proper high/low does **not** constitute BOS. Only a candle that **closes** above (uptrend) or below (downtrend) the level triggers BOS. If only a wick breaks, it's tracked as `wick_high_val` / `wick_low_val` and may trigger an Inducement Shift.

### Color Disambiguation
Each SMC overlay **MUST** have a unique, visually distinct color to avoid chart confusion:

| Overlay | Color | Hex |
|---|---|---|
| Pullback Line | Orange | `#ff9800` |
| Inducement (#) | Yellow | `#ffd600` |
| Inducement Shift (IS) | Cyan | `#00e5ff` |
| BOS | Blue | `#2962ff` |
| ChoCH | Magenta | `#e91e63` |

> **Lesson**: Previously IS and Pullback were both orange, making it impossible to distinguish them on the chart. Always use distinct colors for overlapping elements.

---

## Structure Caching (`structure_service.py`)

### Cache Strategy
- **Cache key**: `{symbol}_{timeframe}.json` stored under `data/structure_cache/`
- **Cache validation**: Compare `last_timestamp` and `total_candles` from the cached file against current data — recompute only on mismatch
- **Performance**: Cache hit provides **< 10ms** response time vs **2-5 seconds** for full recomputation

### When to Invalidate
- New candles fetched (timestamp mismatch)
- Code changes to analysis logic (delete cache files manually or clear `data/structure_cache/`)

```bash
# Clear all cached structures (forces recomputation)
rm -f data/structure_cache/*.json
```

---

## Web Dashboard Tips

### Master Toggle Pattern
When providing multiple layer toggles, always include a single "Master" checkbox that controls all sub-toggles. Use the `class="layer-toggle"` pattern to select all children:

```javascript
function toggleMaster(isChecked) {
    document.querySelectorAll('.layer-toggle').forEach(cb => {
        cb.checked = isChecked;
    });
    toggleLayers();
}
```

### Chart Resize Handling
Always attach a window resize listener to keep the chart responsive:

```javascript
window.addEventListener('resize', () => {
    chart.resize(container.clientWidth, container.clientHeight);
});
```
