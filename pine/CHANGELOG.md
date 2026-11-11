# Changelog — Tradeus Liquidity Toolkit

All notable changes to the **Tradeus Liquidity Toolkit** (`pine/tradeus_liquidity_toolkit.pine`) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased / Current Version] - Pine Script v6

### Added
- **Institutional Liquidity Sweeps Engine (`show_sweeps`):**
  - Real-time detection of smart money liquidity grabs / stop runs.
  - Pivot-based liquidity pool tracking using `ta.pivothigh()` and `ta.pivotlow()`.
  - **Bullish Liquidity Sweep:** Wick below swing low support with close back above the level (`low < swing_low` and `close >= swing_low`).
  - **Bearish Liquidity Sweep:** Wick above swing high resistance with close back below the level (`high > swing_high` and `close <= swing_high`).
  - Visual lines, "Sweep" labels, and customizable candle background highlight (`sweep_highlight_bar`).
  - Automatic swing level invalidation once a candle body closes beyond the level.
  - Dedicated alert conditions: `"Bullish Liquidity Sweep"` and `"Bearish Liquidity Sweep"`.
- **FVG-Paired Order Blocks (`show_obs`):**
  - Footprint detection of institutional origin candles responsible for Fair Value Gaps.
  - Support for both traditional 3-candle gaps (`bar_index - 2`) and inside-bar consolidated base candles (`ref1_bar`).
  - Independent display toggles: `show_bull_obs` (Buy OBs) and `show_bear_obs` (Sell OBs).
  - Invalidated Order Block management: `remove_invalidated_obs` automatically deletes boxes when price closes through the block boundary (`close < ob_bottom` for Buy OB, `close > ob_top` for Sell OB).
  - Dedicated buffer control via `trim_ob_array()` enforcing `max_fvgs` limit.
- **Inversion Fair Value Gaps (iFVG) State Engine:**
  - Implemented `FvgItem` User-Defined Type (UDT) storing `box bx`, `bool is_ifvg`, `int ifvg_bar`, and `bool is_closed`.
  - **Dynamic Inversion Mechanics:**
    - Buy-Side (Bullish) FVG converts to **Bearish iFVG** (Light Orange fill `#ff9800`, fluorescent orange text) when candle closes inside, closes below, or gaps down below the gap.
    - Sell-Side (Bearish) FVG converts to **Bullish iFVG** (Light Blue fill `#2962ff`, fluorescent blue text) when candle closes inside, closes above, or gaps up above the gap.
  - Configurable retention: `remove_closed_ifvgs` option to instantly delete closed iFVGs from chart, or retain the most recent N active iFVGs (`recent_ifvg_keep`, default 25).
- **Price Gaps Module Alerts:**
  - Added alert conditions for `alertInfo.hasOpenedGap()` ("New Gap Appeared") and `alertInfo.hasClosedGap()` ("Gap Closed").
- **Precision Decimal Normalization:**
  - Dynamic decimal rounding function `round_price()` adapting to asset class (5 decimals for Forex & Metals, 2 decimals for Indian Futures & Equities).

### Changed
- **Pine Script Language Version:** Upgraded to `@version=6` with modern type system and method chaining.
- **Fair Value Gaps Styling Overhaul:**
  - Replaced legacy opacity settings with uniform 70% transparency fills, matching borders, and distinct fluorescent label colors (`#00ff00` for Buy FVG, `#ff1744` for Sell FVG, `#00e5ff` for Bullish iFVG, `#ff9100` for Bearish iFVG).
  - Integrated dual detection modes (`fvg_use_inside_bars` toggle for traditional 3-bar vs inside-bar sequence).
- **Memory & Object Management:**
  - Standardized unified buffer trimming (`trim_fvg_array`, `trim_ob_array`) preventing TradingView 500-box overflow errors on high-bar-count charts.
- **Market Structure Engine Alignment:**
  - Synchronized Pine Script logic with Python backend engine (`bos_choch_inducement.py` & `structure_service.py`).
  - Refined multi-trend resolution loop (up to 2 iterations per bar) to immediately process same-bar ChoCH transitions.
  - Added all-time low (ATL) tracking with self-correcting structural reset before trend locking (`htf_locked`).

### Removed
- **Direct Supply & Demand Zone Plotting:**
  - Removed legacy swing-based Supply and Demand zone drawing (`show_zones`, `active_sd_zones`, `draw_supply_zones_in_range`, `draw_demand_zones_in_range`) from the all-in-one toolkit.
  - *Rationale:* Drawing numerous wide swing zones rapidly exhausted TradingView's 500-box limit and created visual chart clutter. High-probability reaction zones are now cleanly provided by the new Order Blocks and Inversion FVG modules, while macro Supply/Demand zones are handled by dedicated scripts and the backend service.

---

## [v1.1.0] - Structural Refinement & Price Gaps Integration

### Added
- **Price Gaps Engine (`show_gaps`):**
  - Real-time gap detection across successive candles based on a 14-bar SMA range deviation threshold (`minimalDeviationInput`).
  - Pine Script User-Defined Types (`Gap`, `AlertInfo`) with object methods (`checkForClose`, `partialClose`, `fullClose`, `delete`).
  - Partial gap closure option (`closeGapsPartially`) shrinking boxes as price penetrates the gap.
  - Max trail length threshold (`limitBoxLengthIntInput`) to prune stale gap boxes.
  - Information table for charts with zero detected gaps.
- **Inside Bar FVG Logic (`fvg_use_inside_bars`):**
  - Option to compute FVGs referenced against mother bars (`ref1_bar`, `ref2_bar`) across multi-bar consolidation.

### Changed
- **Renamed Indicator:** Renamed from `TradeUS SMC Toolkit` to `Tradeus Liquidity Toolkit`.

---

## [v1.0.0] - Initial SMC Baseline

### Added
- **Core Market Structure Engine:**
  - Automatic detection of Break of Structure (BOS) on candle close.
  - Change of Character (ChoCH) trend reversal marking.
  - Inducement (`#`) identification on pullback swing break.
  - Inducement Shift (`IS`) tracking for wick breaks.
- **SMC Dynamic Pullbacks (ZigZag):**
  - Swing high/low zigzag lines with directional state tracking.
- **Inside Bar Consolidation Zones:**
  - Mother bar range projection and consolidation bounding boxes.
- **Buyer vs. Seller Strength:**
  - Real-time candle pressure calculation plotted on the status line and data window.
