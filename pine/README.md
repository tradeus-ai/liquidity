# Tradeus Liquidity Toolkit

The **Tradeus Liquidity Toolkit** is a institutional-grade, all-in-one Smart Money Concepts (SMC) indicator developed in **Pine Script v6** for TradingView. It provides automated mapping of higher-timeframe and execution-timeframe market structure, unmitigated imbalance zones, institutional order blocks, and real-time liquidity sweeps.

The toolkit is engineered for high-probability setups in Indian Futures (NSE) and Forex/Metals markets, following systematic rules for trend identification, liquidity grabs, and market shift confirmations.

---

## Architecture & Modular Design

The toolkit contains 7 independent, fully toggleable modules and real-time momentum metrics:

```
Tradeus Liquidity Toolkit (v6)
├── 1. Market Structure Engine (BOS / ChoCH / Inducement / IS)
├── 2. Institutional Liquidity Sweeps (Stop Hunt Detection)
├── 3. Order Blocks (FVG-Paired Footprints)
├── 4. Fair Value Gaps & Inversion FVGs (FVG / iFVG)
├── 5. SMC Pullbacks (Dynamic ZigZag)
├── 6. Inside Bar Zones (Consolidation Ranges)
├── 7. Price Gaps (Opening / Runaway Gaps)
└── Momentum & Status Line (Buyer / Seller Strength Histogram)
```

---

## Core Modules & Features

### 1. Market Structure Mapping (BOS / ChoCH / Inducement / IS)
Accurately reproduces the algorithmic market structure logic matching the Python backend engine:
- **Inducement (`#`):** Marks the first swing low break in an uptrend (or swing high break in a downtrend). Yellow solid line and label indicate liquidity has been grabbed, confirming the valid structural peak high/low.
- **Break of Structure (BOS):** Confirmed when a candle body **closes** beyond the confirmed structural target high or low. Plotted as a blue solid line with a "BOS" label. Automatically calculates the leg minimum/maximum to establish the new Change of Character (ChoCH) level.
- **Change of Character (ChoCH):** Signals a potential macro trend reversal when price breaches the structural counter-level. Plotted as a magenta line with a "ChoCH" label.
- **Inducement Shift (`IS`):** Detects internal shifts when price wicks beyond a structural level without closing, subsequently breaking an internal pullback swing. Plotted in cyan with an "IS" label.
- **Self-Correcting Anchor:** Automatically tracks the all-time low (ATL) and re-anchors structural calculations if a new lower low forms before the first structural break locks in.
- **Multi-Trend Resolution:** Executes up to 2 iterations per bar to instantly handle candle-level ChoCH reversals and immediate trend shifts.

### 2. Institutional Liquidity Sweeps (New)
Detects smart money liquidity grabs and stop runs around unbroken key swing levels:
- **Pivot Liquidity Pools:** Identifies major swing highs (buy-side liquidity / buy stops) and swing lows (sell-side liquidity / sell stops) using configurable pivot lookback periods (`sweep_pivot_len`).
- **Bullish Sweep:** Triggered when price wicks below an active swing low support pool (`low < swing_low`) but closes back at or above the level (`close >= swing_low`). Indicates a stop hunt and rejection. Marked with a green line, a "Sweep" label, and an optional candle background highlight.
- **Bearish Sweep:** Triggered when price wicks above an active swing high resistance pool (`high > swing_high`) but closes back at or below the level (`close <= swing_high`). Marked with a red line, a "Sweep" label, and an optional candle background highlight.
- **Level Invalidation:** Swing levels are immediately retired once a candle closes cleanly through the level.
- **Dedicated Alerts:** Built-in alerts for both bullish and bearish liquidity sweep events.

### 3. Order Blocks (FVG-Paired) (New)
Identifies the originating institutional candle (Order Block) responsible for creating Fair Value Gaps:
- **Bullish Order Block (Buy OB):** The decisive origin candle preceding a bullish imbalance. Rendered in purple fill (`bull_ob_color`) with a rightward dynamic extension.
- **Bearish Order Block (Sell OB):** The decisive origin candle preceding a bearish imbalance. Rendered in yellow fill (`bear_ob_color`) with a rightward dynamic extension.
- **Dual Support Modes:** Detects OBs using either traditional 3-candle price gaps or inside-bar consolidated base candles (`ref1_bar`).
- **Smart Invalidation:** Option to automatically delete invalidated Order Blocks (`remove_invalidated_obs`) as soon as a candle closes through the block (`curr_close < ob_bottom` for Buy OB; `curr_close > ob_top` for Sell OB).
- **Buffer Management:** Strictly bounded by max display limits to preserve chart responsiveness.

### 4. Fair Value Gaps (FVG) & Inversion FVGs (iFVG) (Enhanced)
A complete imbalance and inversion gap engine:
- **Bullish & Bearish FVGs:** Highlights unmitigated 3-candle imbalances with 70% transparency fills, matching borders, and high-visibility text labels.
- **Inside Bar Sequence Mode:** `fvg_use_inside_bars` allows gap detection across inside-bar clusters, ignoring minor consolidation noise.
- **Inversion FVG (iFVG) Conversion:**
  - When price closes inside, closes below, or gaps down below a **Buy-Side FVG**, it dynamically transforms into a **Bearish iFVG** (Light Orange fill `#ff9800`, fluorescent orange label).
  - When price closes inside, closes above, or gaps up above a **Sell-Side FVG**, it dynamically transforms into a **Bullish iFVG** (Light Blue fill `#2962ff`, fluorescent blue label).
- **iFVG Lifecycle Management:**
  - `remove_closed_ifvgs`: Automatically purges iFVG boxes once closed by subsequent price candles.
  - `recent_ifvg_keep`: Retains only the most recent N active iFVGs when automatic purge is disabled.
- **Array Trimming:** Oldest boxes are safely shifted and deleted to comply with Pine Script memory boundaries.

### 5. SMC Pullbacks (Dynamic ZigZag)
- Maps confirmed swing highs and swing lows through a directional zigzag line.
- Dual-role implementation: Renders visual swing legs (`zigzag_color`) while concurrently feeding validated swing points (`is_sh`, `is_sl`) into the Market Structure Engine.
- Resolves dual-direction bar expansions (outside bars) using open-to-extreme distance metrics.

### 6. Inside Bar Consolidation Zones
- Identifies consolidation periods where successive candles are contained within the high/low of a "mother bar".
- Projects rectangular zones covering the consolidation span until a breakout occurs.
- Includes end-of-chart handling (`barstate.islast`) so currently forming inside bar ranges remain visible in real time.

### 7. Price Gaps (Opening / Runaway Gaps)
- Object-oriented detection using Pine Script User-Defined Types (`Gap`, `AlertInfo`) and methods.
- Dynamic threshold: Filters noise using `minimalDeviationInput` based on a percentage of the 14-bar SMA ATR.
- **Dynamic Extension & Partial Closure:** Extends active gap boundaries forward in real time; supports shrinking the gap boundary when partially filled (`closeGapsPartially`).
- **Trail Length Limiter:** Optional maximum bar duration (`limitBoxLengthIntInput`) to avoid tracking ancient gaps.
- **Exchange Detection Table:** Renders a clean status note if an exchange's 24/7 or continuous data feed produces zero price gaps.

### 8. Buyer/Seller Candle Strength
- Unconditionally calculates relative buyer vs. seller pressure per candle:
  $$\text{Sellers} = \frac{\text{High} - \text{Close}}{\text{High} - \text{Low}} \times 100$$
  $$\text{Buyers} = \frac{\text{Low} - \text{Close}}{\text{High} - \text{Low}} \times 100$$
- Plotted directly on the TradingView Status Line and Data Window as a 3px histogram (Lime for buyers, Red for sellers).

---

## Design Evolution & Note on Supply/Demand Zones

> [!NOTE]
> In earlier indicator revisions, raw swing-based Supply and Demand zones were rendered directly on the chart. To eliminate visual clutter and prevent hitting TradingView's strict 500-box limit, the toolkit now focuses on **FVG-paired Order Blocks** and **Inversion FVGs (iFVG)** for high-precision reaction zones. Macro supply and demand zones remain available in our standalone scripts and Python market structure services.

---

## TradingView Alerts

The toolkit exposes 4 built-in alert conditions for automated notifications or webhook execution:

| Alert Name | Trigger Condition | Message / Description |
|---|---|---|
| **Bullish Liquidity Sweep** | `bull_sweep_now` | `"Bullish Liquidity Sweep: Stops grabbed below support!"` |
| **Bearish Liquidity Sweep** | `bear_sweep_now` | `"Bearish Liquidity Sweep: Stops grabbed above resistance!"` |
| **New Gap Appeared** | `alertInfo.hasOpenedGap()` | `"A new gap has appeared."` |
| **Gap Closed** | `alertInfo.hasClosedGap()` | `"A gap was closed."` |

---

## Input Settings & Customization Guide

### Module Toggles
| Input | Type | Default | Description |
|---|---|---|---|
| `Show Inside Bar Zones` | bool | `true` | Display consolidated inside bar boxes |
| `Show Fair Value Gaps (FVG)` | bool | `true` | Display Bullish/Bearish FVGs and iFVGs |
| `Show SMC Pullbacks (ZigZag)` | bool | `true` | Display swing zigzag lines |
| `Show Gaps` | bool | `true` | Display opening / runaway gap boxes |
| `Show Market Structure` | bool | `true` | Display BOS, ChoCH, Inducement (#), and IS |
| `Show Liquidity Sweeps` | bool | `true` | Display institutional sweep lines & labels |
| `Show Order Blocks` | bool | `true` | Display FVG-paired Order Blocks |

### Liquidity Sweeps Settings
| Input | Type | Default | Description |
|---|---|---|---|
| `Pivot Lookback` | int | `5` | Bars required to confirm a swing pivot (min: 2, max: 50) |
| `Max Active Swing Levels` | int | `10` | Maximum unbroken swing levels to track simultaneously |
| `Bullish Sweep Color` | color | `#00e676` | Line and label color for bullish sweeps |
| `Bearish Sweep Color` | color | `#ff5252` | Line and label color for bearish sweeps |
| `Highlight Sweep Bars` | bool | `true` | Highlight background on the sweep trigger candle |

### Fair Value Gaps & Inversion FVGs Settings
| Input | Type | Default | Description |
|---|---|---|---|
| `Show Bullish FVGs (Buy)` | bool | `true` | Toggle buy-side FVG boxes |
| `Show Bearish FVGs (Sell)` | bool | `true` | Toggle sell-side FVG boxes |
| `Use Inside Bar Logic for FVG` | bool | `true` | Enable inside bar reference filtering for FVGs |
| `Max Boxes to display` | int | `50` | Buffer limit for active FVG/iFVG/OB boxes |
| `Remove Closed iFVGs from chart` | bool | `true` | Remove iFVG once closed by subsequent candle |
| `Recent iFVGs to keep` | int | `25` | Keep most recent N iFVGs if removal is disabled |
| `Buy Side FVG Box Fill / Border` | color | `#4caf50 (70%)` | Green fill and border for bullish FVGs |
| `Sell Side FVG Box Fill / Border` | color | `#f44336 (70%)` | Red fill and border for bearish FVGs |
| `Bullish iFVG Box Fill / Border` | color | `#2962ff (70%)` | Light blue fill and border for bullish iFVGs |
| `Bearish iFVG Box Fill / Border` | color | `#ff9800 (70%)` | Light orange fill and border for bearish iFVGs |

### Order Blocks Settings
| Input | Type | Default | Description |
|---|---|---|---|
| `Show Bullish OBs (Buy)` | bool | `true` | Toggle buy-side Order Blocks |
| `Show Bearish OBs (Sell)` | bool | `true` | Toggle sell-side Order Blocks |
| `Remove Invalidated Order Blocks` | bool | `true` | Automatically delete OB when closed through |
| `Bullish OB Color` | color | `#9c27b0 (75%)` | Fill color for bullish Order Blocks |
| `Bearish OB Color` | color | `#ffeb3b (75%)` | Fill color for bearish Order Blocks |

### Price Gaps Settings
| Input | Type | Default | Description |
|---|---|---|---|
| `Close Gaps Partially` | bool | `false` | Shrink gap boxes as price enters gap zone |
| `Max Number of Gaps` | int | `15` | Maximum active price gaps to track |
| `Minimal Deviation (%)` | float | `30.0` | Gap threshold as % of 14-period SMA high-low range |
| `Limit Max Gap Trail Length` | bool | `false` | Enable bar length cap for gap boxes |
| `Max Trail Length` | int | `300` | Bar count threshold before forcing gap closure |

---

## How to Trade With the Toolkit

1. **Top-Down Bias & Structure (Daily / 4H):**
   - Identify market trend via confirmed **BOS** and **ChoCH** events.
   - Confirm valid swing highs and lows marked by **Inducement (`#`)**.
2. **Zone Identification:**
   - Locate active **Order Blocks** and unmitigated **FVGs / iFVGs** at key structural extremes.
   - Note key price gaps or consolidated inside bar clusters resting within the bias path.
3. **Execution Timeframe Confirmation (15m NSE / 1h Forex):**
   - Wait for price to tap into the HTF zone or sweep an active liquidity pool (**Bullish/Bearish Liquidity Sweep**).
   - Enter on lower-timeframe structural shift (ChoCH / iFVG reclaim) with stop-loss placed beyond the sweep wick.
