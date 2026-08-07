# Smart Money Concepts (SMC) Market Structure

This document explains the core Smart Money Concepts (SMC) logic implemented in `bos_choch_inducement.py` and how it identifies critical market shifts. 

## The Problem

Financial markets do not move in straight lines; they move in waves. Retail traders often misidentify minor pullbacks as major structural shifts, leading to premature entries (e.g., buying a "breakout" that is actually a liquidity sweep). The SMC engine solves this by rigorously defining what constitutes a true structural high or low, ensuring that we only trade confirmed structural breaks (BOS) or major trend reversals (ChoCH).

## The Approach

The engine processes daily (HTF) candlestick data and identifies the following key structural events:

1. **Pullbacks**: Temporary retracements in the current trend (Swing Highs and Swing Lows).
2. **Inducement (IDM)**: In an uptrend, after a new high is formed, price must pull back and break a recent swing low to confirm that high as a **Proper High**. This liquidity sweep is the Inducement.
3. **Break of Structure (BOS)**: Once a Proper High is confirmed by an IDM, a candle **body close** above this Proper High confirms a continuation of the trend. 
4. **Inducement Shift (IS)**: If price sweeps the Proper High but **fails to close above it** (a wick break), the Proper High is invalidated and shifted to the new wick extreme. The engine then looks for a *new* pullback to be broken. When this new pullback is broken, it is marked as an **Inducement Shift (IS)**, re-confirming the new wick extreme as the Proper High.
5. **Change of Character (ChoCH)**: The major structural level that flips the macro trend. In an uptrend, this is the lowest point of the leg that caused the most recent BOS. If price breaks below this level, the trend flips to bearish.

## Trade-offs

- **Strict Confirmation vs. Lag**: By requiring candle body closes for a BOS and wick breaks triggering an Inducement Shift, the engine lags behind pure price action. We trade early entries for higher probability setups.
- **Complexity**: Tracking cycles (from peak to peak) requires maintaining state across candles (e.g., `wick_high_val`, `inducement_done`), making the single-pass algorithm complex.

## Reference: `analyze_htf_structure`

The primary interface for this module is the `analyze_htf_structure(df)` function.

### Inputs
- `df`: A Pandas DataFrame containing OHLC data and pre-computed boolean flags `is_swing_high` and `is_swing_low` for every candle.

### Outputs
Returns a dictionary with the following keys:
- `events`: A list of structural event dictionaries to be plotted on the UI.
- `zones`: A list of identified Demand and Supply zones (historical and active).
- `current_state`: The current macro trend (`1` for Uptrend, `-1` for Downtrend) and whether `inducement_done` is true.

### Event Format
Each event in the `events` list follows this structure:
```json
{
    "type": "IS",                // Type of event: IDM, IS, BOS, or CHOCH
    "label": "IS",               // Display label for the chart
    "start_time": 1690000000,    // Unix timestamp of the pullback low/high being broken
    "start_val": 19500.50,       // Price level of the structure point
    "end_time": 1690100000,      // Unix timestamp of the candle breaking the structure
    "end_val": 19500.50,         // Price level extended horizontally
    "color": "#00e5ff"           // Hex color code for rendering
}
```

### Color Conventions
- **IDM (#)**: `#ffd600` (Yellow)
- **Inducement Shift (IS)**: `#00e5ff` (Cyan)
- **BOS**: `#2962ff` (Blue)
- **ChoCH**: `#e91e63` (Pink)
