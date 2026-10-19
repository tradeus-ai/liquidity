# Tradeus Reaction-Filtered SMC Strategy Documentation

## Overview
**`tradeus_reaction_strategy.pine`** is a dedicated TradingView Pine Script v6 strategy designed for high-probability Smart Money Concepts (SMC) order execution.

Rather than flooding the chart with raw Order Blocks (OBs) and Fair Value Gaps (FVGs), candidate zones are monitored silently in background memory. A setup is **only materialized on the chart and executed** when an institutional reaction sequence is confirmed.

---

## The Reaction Pipeline

```
[STANDARD OB RETEST PATH]                              [ATH / ATL REVERSAL PATH]
[Silent Candidate OB] + [Silent Opposite FVG]          Market reaches ATH / ATL Peak/Trough
              │                                                      │
              ▼                                                      ▼
   Price Retests / Touches OB                          Price Closes Inside Recent Opposite FVG
   (Records touch_bar, touch_low, touch_high)          (Bullish FVG at ATH -> Sell; Bearish FVG at ATL -> Buy)
              │                                                      │
              ├───► [RETEST BREACH CHECK [D7]]                       │
              │     If low < touch_low / high > touch_high           │
              │     ──► Abandons retest, looks at NEXT OB            │
              ▼                                                      │
   ┌─────────────────────────────────────────────────┐               │
   │ CANDLE SEPARATION GATE [D6]                     │               │
   │ Reaction CANNOT be same candle as touch:        │               │
   │          bar_index > ob.last_touch_bar          │               │
   └─────────────────────────────────────────────────┘               │
              │                                                      │
              ▼                                                      │
   Opposite FVG Inverted [D4]                                        │
   (Candle closes inside or beyond opposite FVG)                     │
              │                                                      │
              └───────────────────────┬──────────────────────────────┘
                                      │
                                      ▼
                           >>> REACTION CONFIRMED <<<
                                      │
             ┌────────────────────────┴────────────────────────┐
             │                                                 │
             ▼                                                 ▼
[STANDARD OB TARGETING]                               [ATH / ATL REVERSAL TARGETING]
• Flat check (1 trade at a time) [D3]                 • Flat check (1 trade at a time) [D3]
• Swings strictly left of touch (bar < ob.touch_bar)  • Swings strictly left of ATH/ATL (bar < ath_bar)
  - Target 1: 1st unbreached swing (pullback origin)    - Target 1: 1st unbreached pullback swing
  - Target 2: 2nd unbreached swing (structural wave)    - Target 2: 2nd low pullback (ATH Sell)
  - Abort if < 2 unbreached swings found [D2]           - Target 2: 2nd high pullback (ATL Buy)
• Stop Loss: Retested candle extreme ± buffer [D7]      - Abort if < 2 unbreached swings found
• Full Exit Limit at Target 2                         • Stop Loss: ATH high + buffer / ATL low - buffer
• Visuals kept on chart if SL hit [D9]                • Full Exit Limit at Target 2 (2nd Pullback)
```

---

## Key Strategy Mechanics

### 1. Retest Extreme Tracking & Next OB Search [D7]
- On the first candle that wicks or trades into the OB, the strategy records `touch_low` and `touch_high`.
- If on subsequent bars prior to reaction price penetrates beyond the first retest candle's extreme (`low < touch_low` for Buy, `high > touch_high` for Sell), the active retest attempt is flagged as breached.
- The strategy immediately abandons this retest and evaluates subsequent candidate OBs.
- The OB itself remains valid until structural invalidation occurs (candle close below OB bottom for Buy, or close above OB top for Sell).

### 2. Candle Separation Gate [D6]
- A frequent trap is a single giant volatility candle that sweeps the OB and closes inside the opposite FVG within the same bar.
- The strategy strictly enforces: `bar_index > ob.last_touch_bar`.
- Any bar that touches the OB zone updates `last_touch_bar := bar_index`, prohibiting that bar from triggering the entry. The reaction must occur on a separate subsequent candle.

### 3. Loosened Opposite FVG Inversion [D4]
- Standard SMC accounts for strong impulse reactions that close through and beyond the opposite FVG.
- A Bearish FVG is inverted if `close >= fvg.bottom`.
- A Bullish FVG is inverted if `close <= fvg.top`.

### 4. Target Discovery Left of First Retest Candle [D2, D8]
- Targets are dynamically discovered from confirmed SMC Pullback swing points.
- The scanner only inspects swings formed **strictly to the left of the first retested candle** (`s_bar < ob.touch_bar`).
- Swings formed during the consolidation inside the OB are ignored for macro target discovery.
- **Target 1:** 1st most recent unbreached swing (the immediate pullback origin).
- **Target 2:** 2nd most recent unbreached swing (prior structural swing wave).
- **Institutional Quality Gate [D2]:** If fewer than 2 unbreached swings are found above entry (Long) or below entry (Short), the setup is **aborted completely**.

### 5. Visual Retention on Stop Loss [D9]
- When a trade stops out at Stop Loss, the materialized OB box, iFVG box, and Target lines are **strictly kept on the chart**.
- Boxes and lines are never deleted on loss; they are pruned exclusively by the global FIFO queue (`max_display = 15`), preserving historical context for trader review.

### 6. Indian Markets Session Timing & Canonical IST Execution (UTC+5:30)
The strategy implements a strict **IST Execution Framework** anchored to `"Asia/Kolkata"` (UTC+5:30):
- **Timezone Independence:** Regardless of whether your TradingView chart display timezone is set to UTC, New York (EST), London, or Tokyo, all sessions, timers, and order executions run strictly in **Indian Standard Time (IST, UTC+5:30)**.
- **Weekday Guard (`:23456`):** All session strings are suffixed with `:23456`, restricting order executions strictly to Monday through Friday and preventing anomalous fills on weekend test feeds.
- **Decoupled Entry Window vs Intraday MIS Square-Off Window:**
  - **Trade Entry Windows:** Restrict *new trade setups* to high-liquidity momentum periods:
    - *NSE Morning Momentum:* `09:15 to 11:15 am IST` (`0915-1115`).
    - *NSE Full Day:* `09:15 am to 03:15 pm IST` (`0915-1515`).
    - *MCX Evening Active:* `06:15 pm to 11:00 pm IST` (`1815-2300`).
    - *Custom IST Window:* Configurable user hours in `"Asia/Kolkata"`.
  - **Intraday MIS Square-Off Cutoffs:** When `Square-off at Session End (Intraday MIS)` is enabled, open positions are **held throughout the day** until they reach Target 2 or Stop Loss, and are only auto-closed if still open at official broker cutoff:
    - *NSE MIS Cutoff:* `03:15 to 03:30 pm IST` (`1515-1530`).
    - *MCX MIS Cutoff:* `11:25 to 11:30 pm IST` (`2325-2330`).
- **Transparent IST Audit Trail:** Every order, target exit, stop-out, and alert message includes an explicit IST timestamp (e.g. `[Long @ 10:15 IST]`, `[MIS EOD Square-off @ 15:15 IST]`).

### 7. Position Sizing (1% per Trade)
- **1% Risk of Equity (SL-Based) [Default]:** Dynamically sizes contracts so that if the Stop Loss is hit, the account loses exactly 1% of equity. Respects contract lot steps (e.g., NIFTY=25/50, BANKNIFTY=15, CRUDEOIL=100).
- **1% Capital Allocation:** Limits trade value to 1% of total account capital.
- **Pine Default:** Default strategy equity allocation is set to 1.0% in strategy settings.

### 8. All-Time High (ATH) & All-Time Low (ATL) Reversal Logic
When the market trades into uncharted territory (All-Time Highs or All-Time Lows), traditional OB retests cannot find prior structural swing targets above/below the market. The strategy includes a dedicated institutional reversal engine:

- **ATH Sell Setup (Reversal from All-Time High):**
  - **Trigger Condition:** Market is at an All-Time High (`current_ath_high` at `current_ath_bar`).
  - **Reaction Signal:** Price closes inside the most recent active Bullish FVG formed near or before the ATH (`curr_close <= fvg.top and curr_close >= fvg.bottom`).
  - **Trade Direction:** Enters **Sell (Short)** trade.
  - **Stop Loss:** Placed strictly above the ATH peak: `current_ath_high + (sl_buffer_ticks * syminfo.mintick)`.
  - **Trade Target:** The **2nd low pullback** left of the ATH peak (`final_t2 = math.min(t1_price, t2_price)`).
  - **Quality Gate:** If fewer than 2 confirmed unbreached SMC swing lows exist left of the ATH peak, the entry is aborted (or uses 1:2 R:R fallback if enabled).
  - **Deduplication:** `last_ath_traded_bar` prevents multiple entries on the same ATH peak.

- **ATL Buy Setup (Reversal from All-Time Low):**
  - **Trigger Condition:** Market is at an All-Time Low (`current_atl_low` at `current_atl_bar`).
  - **Reaction Signal:** Price closes inside the most recent active Bearish FVG formed near or before the ATL (`curr_close >= fvg.bottom and curr_close <= fvg.top`).
  - **Trade Direction:** Enters **Buy (Long)** trade.
  - **Stop Loss:** Placed strictly below the ATL trough: `current_atl_low - (sl_buffer_ticks * syminfo.mintick)`.
  - **Trade Target:** The **2nd high pullback** left of the ATL trough (`final_t2 = math.max(t1_price, t2_price)`).
  - **Quality Gate:** If fewer than 2 confirmed unbreached SMC swing highs exist left of the ATL trough, the entry is aborted (or uses 1:2 R:R fallback if enabled).
  - **Deduplication:** `last_atl_traded_bar` prevents multiple entries on the same ATL trough.

### 9. Visual Cleanliness & Drawing Lifespan Rules
To prevent chart clutter and enable crystal-clear trade visualization:
- **No Infinite Rays (`extend.none`):** Target and Stop Loss lines do NOT project endlessly into future bars.
- **OB Box Lifespan:** The Order Block box starts at the OB formation candle (`ob.start_bar`). It extends dynamically while the trade is live, and **ends strictly on the candle where Target 2 is hit or Stop Loss is hit**.
- **Target & SL Line Lifespans:**
  - **T1 Line:** Present only from the entry candle until the candle where Target 1 is hit (or when SL is hit).
  - **T2 Line & SL Line:** Present only from the entry candle until the resolution candle where Target 2 or Stop Loss is hit.
- **FVG Box Lifespan:** The Fair Value Gap box is shown **strictly until the first candle that closes inside the FVG** (`right = fvg.inversion_bar`). It never extends across future candles.

### 10. Indian Equities & Futures Execution (BHEL, NSE & BSE)
- **Account Capital & Margin:** Strategy is initialized with `initial_capital = 1,000,000` (10 Lakhs INR) and `margin_long/short = 0`. This eliminates TradingView capital/margin order rejections on large futures contracts like `BHEL` (lot size 2,625 shares requiring ~6.5 Lakhs capital).
- **Session Auto-Detect:** For NSE and BSE symbols, Auto-Detect defaults to Full Day (`09:15 - 15:15 IST`), allowing trades throughout the day rather than stopping at 11:15 AM.
- **Timeframe Flexibility:** Non-intraday timeframes (Daily `1D`, Weekly `1W`) automatically bypass intraday session windows.
- **Target Swing Count:** Configurable `Min Swings Required for Target` (1 or 2) with optional `1:2 R:R Fallback` ensures valid trades are never discarded on strongly trending stocks with sparse historical swings.

---

## Input Settings & Configuration

| Parameter | Default | Group | Description |
|-----------|---------|-------|-------------|
| `Enable ATH / ATL Reversal Mode` | `true` | ATH / ATL Reversal Strategy | Toggles ATH Sell and ATL Buy reversal engine. |
| `ATH/ATL Scope` | `Chart Lifetime ATH/ATL` | ATH / ATL Reversal Strategy | Scope: Chart Lifetime vs Rolling Lookback (200 / 500 bars). |
| `Max Bars After ATH/ATL Peak/Trough` | `30` | ATH / ATL Reversal Strategy | Max bars elapsed from ATH/ATL within which the FVG close must occur. |
| `ATH/ATL FVG Close Trigger` | `Inside FVG (Close between Top & Bottom)` | ATH / ATL Reversal Strategy | Trigger criteria: Inside FVG vs Inside or Beyond FVG. |
| `Show All FVGs (Debug Mode)` | `false` | Display | When enabled, draws all raw FVGs on chart for inspection. |
| `Show All OBs (Debug Mode)` | `false` | Display | When enabled, draws all raw OBs on chart for inspection. |
| `Max Reaction Setups Displayed` | `50` | Display | FIFO capacity queue limit for materialized setups on chart (Pine max 500). |
| `Max Candidate OBs/FVGs in Memory` | `500` | Display | Memory queue size for unreacted candidate OBs and FVGs. |
| `Show SMC Pullback ZigZag` | `true` | Display | Renders the confirmed SMC pullback swing legs. |
| `Show Target & SL Price Labels` | `true` | Display | Displays price tags on Target 1, Target 2, and Stop Loss lines. |
| `Market Session Mode` | `Auto-Detect (NSE / MCX) [IST]` | Market Sessions (India - IST UTC+5:30) | Restricts reaction entries to official Indian trading sessions evaluated in `Asia/Kolkata`. |
| `NSE Morning Momentum Window (IST)` | `0915-1115` | Market Sessions (India - IST UTC+5:30) | Opening momentum window (09:15 to 11:15 am IST). |
| `NSE Full Day Window (IST)` | `0915-1515` | Market Sessions (India - IST UTC+5:30) | Full day trading window up to broker cutoff (09:15 am to 03:15 pm IST). |
| `MCX Session Window (IST)` | `1815-2300` | Market Sessions (India - IST UTC+5:30) | MCX evening active window (06:15 pm to 11:00 pm IST). |
| `Custom Session Window (IST)` | `0915-1515` | Market Sessions (India - IST UTC+5:30) | Custom entry window evaluated in `Asia/Kolkata` timezone. |
| `Highlight Entry Session Window` | `true` | Market Sessions (India - IST UTC+5:30) | Color-coded background during active entry windows. |
| `Square-off at 3:30 PM (Unless Close to T2)` | `true` | Market Sessions (India - IST UTC+5:30) | Auto squares off open positions at official market close (15:15-15:30 IST for NSE, 23:25 IST for MCX), UNLESS the trade has reached near Target 2. |
| `T2 Proximity for Overnight Carryforward (%)` | `80.0` | Market Sessions (India - IST UTC+5:30) | If open trade has achieved at least this % of the distance towards Target 2 by 3:15-3:30 PM IST, carry the position forward overnight. Otherwise, close immediately on the same day. |
| `NSE MIS Square-Off Window (IST)` | `1515-1530` | Market Sessions (India - IST UTC+5:30) | Official NSE broker square-off cutoff window (03:15 pm to 03:30 pm IST). |
| `MCX MIS Square-Off Window (IST)` | `2325-2330` | Market Sessions (India - IST UTC+5:30) | Official MCX broker square-off cutoff window (11:25 pm to 11:30 pm IST). |
| `Position Sizing Mode` | `1% Risk of Equity (SL-Based)` | Position Sizing & Risk | Dynamic 1% risk sizing vs capital allocation vs fixed lots. |
| `Risk / Allocation % per Trade` | `1.0` | Position Sizing & Risk | Percentage of account equity per trade (default 1.0%). |
| `Futures Lot Size` | `1` | Position Sizing & Risk | Minimum lot step for Indian Futures (e.g. NIFTY=25/50, BANKNIFTY=15, CRUDEOIL=100, BHEL=2625). |
| `SL Buffer (ticks beyond retested candle)` | `5` | Strategy | Extra ticks added beyond the retest candle's extreme for Stop Loss. |
| `OB Invalidation Criteria` | `Wick Breach (Low < OB Low / High > OB High)` | Strategy | Rule 1: Invalidate OB permanently if price wick breaches below OB Low (Bullish) or above OB High (Bearish). |
| `OB Mitigation Threshold` | `100% Extreme (OB Bottom for Buy / Top for Sell)` | Strategy | Rule 6: Defines when an OB is fully mitigated: 100% Extreme vs 50% Mean Threshold vs Breach Only. |
| `Max Reactions per Order Block` | `0` | Strategy | Rule 6: Max reaction entries on a single OB before retirement (`0 = Unlimited` until fully mitigated). |
| `Max New Entries Allowed Per Day` | `1` | Strategy | Rule 2: Strictly limits new trade entries initiated on a single calendar day (default: 1). |
| `Action on Opposite OB Reaction` | `Exit Current Trade (Strictly 1 Entry & 1 Exit)` | Strategy | Opposite OB policy: Exit trade only (Strictly 1 Entry & 1 Exit) vs Reverse into opposite direction. |
| `Block Entry if Candle Reaches Other OB` | `true` | Strategy | Rule 5: If reaction candle's low/high reaches into another touched or untouched OB, do not take entries on that side. |
| `Other OB Scope Filter` | `Any Other OB (Opposite or Same Direction)` | Strategy | Scope: Blocks entry if candle reaches ANY other valid OB vs Opposite Direction OBs Only. |
| `Include Prior Reacted OBs in Filter` | `false` | Strategy | If true, also treats prior reacted OBs as obstacles. If false (default), only checks active unconsumed candidate OBs. |
| `Use Inside Bar Logic for FVG & OB` | `true` | Strategy | Absorbs inside bars so FVGs and OBs anchor to true mother candles. |
| `Standard OB FVG Inversion Trigger` | `Inside or Beyond FVG` | Strategy | Trigger criteria: Inside or Beyond FVG vs strictly Inside FVG. |
| `Min Swings Required for Target` | `1` | Strategy | Minimum unbreached swings required to establish targets (1 = single swing allowed, 2 = dual swings required). |
| `Allow 1:2 R:R Fallback if No Swing Target` | `true` | Strategy | If enabled, uses 1:1.5 (T1) and 1:2.0 (T2) R:R target when no unbreached swing is available left of retest. |
| `Allow Reversal on Opposite OB Reaction` | `true` | Strategy | If enabled and a trade is active, a confirmed reaction at an opposite Order Block will close the current trade early. |
| `Stop Trading for Day if SL Hit` | `true` | Strategy | If a trade hits Stop Loss on a given day, no further new entries are taken on that day. |

---

## Conflict Invalidation: Candle Reaching Other Touched / Untouched OB (Rule 5)

A major institutional trap occurs when a reaction candle bounces off an Order Block, but its wick or extreme immediately reaches into another Order Block:
1. **The Opposing Supply/Demand Trap:**
   - **Buy Reaction (Bullish OB):** Price touches Bullish OB. The reaction candle forms and inverts Bearish FVG, but its **HIGH reaches into a Bearish Order Block** (touched or untouched) situated above.
   - **Trap:** Buying at the close of this candle means buying directly into supply resistance that was just mitigated.
   - **Action:** **Do not take entries on that side.** Long entry is aborted.
   - **Sell Reaction (Bearish OB):** Price touches Bearish OB. The reaction candle forms and inverts Bullish FVG, but its **LOW reaches into a Bullish Order Block** (touched or untouched) situated below.
   - **Trap:** Selling at the close of this candle means selling directly into demand support that was just mitigated.
   - **Action:** **Do not take entries on that side.** Short entry is aborted.
2. **Same-Side Overlap / Deeper Zone Conflict:**
   - When set to `"Any Other OB (Opposite or Same Direction)"` (default): If the candle's low/high reaches *any other* candidate OB (touched or untouched), the setup is skipped to avoid ambiguous, colliding, or stacked zones.
3. **Touched vs Untouched OBs:**
   - The filter inspects both untouched OBs (fresh liquidity zones) and touched OBs (zones already retested, including prior reacted and partially mitigated zones).
4. **Dual Candle Evaluation (Reaction Candle & Touch Candle):**
   - The filter inspects the **current reaction candle** (`bar_index`) AND the **anchor touch candle** (`anchor_touch_bar`). If either candle's low or high reaches into another touched or untouched OB, conflict is declared.
5. **Side-Wide Lockout on Conflict:**
   - If a conflict is detected on an OB reaction, the entire side (`block_buy_side` for Longs, `block_sell_side` for Shorts) is locked for that candle, ensuring no fallback or older OBs take entries on that side.

---

## Multi-Reaction Lifecycle until Full Mitigation (Rule 6)

In Smart Money Concepts (SMC), an Order Block is not a single-use disposable zone. Until an OB is **fully mitigated** (or structurally breached), institutional liquidity remains inside the zone and the market can revisit and produce valid reaction entries across subsequent retest cycles.

### 1. Full Mitigation Definitions (`ob_mitigation_mode`)
- **`100% Extreme (OB Bottom for Buy / Top for Sell)` [Default]:**
  - **Bullish OB:** Fully mitigated when price reaches the deepest boundary: `curr_low <= ob.bottom`.
  - **Bearish OB:** Fully mitigated when price reaches the deepest boundary: `curr_high >= ob.top`.
  - Once touched at its extreme, all latent orders are consumed, marking `ob.is_fully_mitigated := true` and retiring the OB.
- **`50% Mean Threshold (Equilibrium Midpoint)`:**
  - Fully mitigated when price reaches the 50% midpoint of the OB range: `(ob.top + ob.bottom) / 2.0`.
- **`Breach Invalidation Only`:**
  - The OB remains active for reactions indefinitely until structurally violated/breached.

### 2. Retest Wave Tracking & Multi-Reaction Gating
- **Distinct Retest Waves:** When price pulls away from the OB and re-enters (`bar_index > ob.last_touch_bar + 1`), a new retest wave begins (`ob.retest_touch_bar := bar_index`), resetting the wave's extreme low/high.
- **Separation Gate:** The reaction candle must occur strictly after the touch bar for that wave (`bar_index > anchor_touch_bar`, where `anchor_touch_bar = not na(ob.retest_touch_bar) ? ob.retest_touch_bar : ob.touch_bar`). The candle that re-enters the OB cannot also be the trigger candle.
- **Retest Wave Requirement for Re-reactions:** When `ob.reactions_count > 0`, taking another reaction requires price to have left the OB and started a fresh retest wave strictly after the last reaction (`ob.retest_touch_bar > ob.last_reaction_bar`). This prevents double-entry spam during the same retest wave.
- **Target Discovery Across Waves:** Swing highs/lows are scanned strictly left of the current wave's `anchor_touch_bar`. Any swing high formed during intermediate bounces between reaction 1 and reaction 2 becomes a valid target for reaction 2!
- **Retirement:** Once `is_fully_mitigated` or `is_invalidated` becomes true, or `reactions_count >= max_reactions_per_ob` (if set > 0), the OB is retired from active scanning.

---

## Order Block Low / High Breach Invalidation (Rule 1)

In Smart Money Concepts, an Order Block is defined by the high and low boundaries of its founding candle (`ob.bottom` to `ob.top`):
1. **Bullish OB Breach (Bottom / Low Pierced):**
   - If market price trades below the OB's lowest price (`curr_low < ob.bottom`), the Order Block is compromised.
   - It is immediately and permanently marked `ob.is_invalidated := true` and its candidate box is deleted.
   - **No entries will be taken on this OB.**
2. **Bearish OB Breach (Top / High Pierced):**
   - If market price trades above the OB's highest price (`curr_high > ob.top`), the Order Block is compromised.
   - It is immediately and permanently marked `ob.is_invalidated := true` and its candidate box is deleted.
   - **No entries will be taken on this OB.**
3. **Execution Guard:**
   - Both the candidate monitoring loop and pre-entry trigger blocks verify `ob_low_breached` / `ob_high_breached` on the trigger bar.
   - Stop Loss is positioned at `math.min(ob.touch_low, ob.bottom) - buffer` (Long) and `math.max(ob.touch_high, ob.top) + buffer` (Short) to defend the entire structural block.

---

## Daily Trade Frequency & Lifecycle Limits (Rule 2)

To enforce strict discipline and prevent overtrading or drawdown compounding, the strategy tracks the entire daily trade lifecycle with hard gates:

### Scenario A: Flat at Day Open — "Strictly 1 Entry and 1 Exit per Day"
- If the day starts with zero open positions (`strategy.position_size == 0` at 09:15 IST):
  - **1st Entry:** The first valid reaction triggers an entry (`day_entries_count := 1`).
  - **Trade Active:** No additional entries or pyramiding permitted.
  - **1st Exit:** The trade eventually exits via Target 2 limit, Stop Loss, Opposite OB exit, or 3:30 PM MIS square-off.
  - **Lockout:** Upon exit, `day_trade_completed := true`. All scanning and entry triggers are locked for the remainder of that day.
  - **Result:** Strictly **1 entry and 1 exit** for the entire day.

### Scenario B: Overnight Position at Day Open — "1 Exit & Entry + 1 Exit on Same Day"
- If a position was carried forward overnight from yesterday (`started_day_with_position = true`, `day_entries_count = 0` at 09:15 IST):
  - **1st Exit:** The overnight trade hits Target 2, Stop Loss, or an early exit (`day_exits_count := 1`).
  - **1st Fresh Entry:** Because today has initiated 0 new trades (`day_entries_count < max_daily_entries`), the system is eligible to take **one fresh entry today** (`& entry`).
  - **2nd Exit:** When this newly initiated trade reaches its exit (+ 1 exit), `day_trade_completed := true`.
  - **Lockout:** All further entries are locked for the rest of the day.
  - **Result:** Strictly **1 exit (overnight) & 1 entry + 1 exit** on the same day.

### Opposite OB Action Toggle:
- **`Exit Current Trade (Strictly 1 Entry & 1 Exit)` [Default]:** When an opposite OB reaction occurs, the active trade is closed immediately to protect capital. No opposite trade is opened, locking the day at 1 entry and 1 exit.
- **`Reverse Position (1 Exit & Entry + 1 Exit)`:** When an opposite OB reaction occurs, the active trade is closed (1 exit) and reversed into the new direction (& entry), running until its final resolution (+ 1 exit).

---

## Active Trade Reversal Mechanics (Opposite Order Block Reaction)

When a trade is active (`strategy.position_size != 0`) and price has not yet reached Target 2 or Stop Loss:
1. **Opposite OB Touch & Reaction:** If the market enters an opposite Order Block (e.g., Bearish OB during an active Long, or Bullish OB during an active Short) and on a subsequent bar confirms an impulse close inside/beyond the opposite FVG/iFVG:
   - **Early Exit:** The current position is exited at market close on the reaction bar (`[Rev Short @ HH:MM IST]` / `[Rev Long @ HH:MM IST]` or `[Opposite OB Exit @ HH:MM IST]`).
   - **Visual Finalization:** The previous trade's visual setup is cleanly finalized and frozen on chart:
     - The OB box right edge is pinned to the reversal bar (`bar_index`).
     - Target 1, Target 2, and Stop Loss lines are terminated at `bar_index` (no infinite line extensions).
   - **Opposite Entry (if reversal mode enabled):** Enters the new trade in the reversed direction with its own SL, Target 1, and Target 2.
2. **Pyramiding Protection:** If an active Long receives another Bullish OB reaction, it is strictly ignored (no pyramiding). Symmetrically, an active Short will never pyramid on another Bearish OB reaction.
3. **ATH / ATL Symmetry:** Reversal also functions when an active Long runs into an ATH FVG reaction, or an active Short runs into an ATL FVG reaction.

---

## Daily Risk Rules & Overnight Carryforward Rules

1. **Daily Stop on SL Hit (Rule 3):**
   - If a trade hits Stop Loss on any calendar day, `stop_trading_on_daily_sl` blocks any subsequent trade entries for the remainder of that day.
   - Resets automatically at 00:00 IST / market open of the next trading day.

2. **3:30 PM EOD Square-Off vs T2 Carryforward (Rule 4):**
   - At market close (15:15–15:30 IST for NSE, 23:25–23:30 IST for MCX):
   - The strategy checks if the current position is **very close to Target 2** ($\ge 80\%$ progress towards T2).
   - If **close to Target 2**: the position is carried forward overnight to allow hitting the T2 limit order.
   - If **NOT close to Target 2**: the position is closed immediately on the same day (`[EOD Exit (Not Near T2) @ HH:MM IST]`) and visuals are cleanly frozen at market close.



---

## Order Execution Details

- **Type:** Single-position with active opposite-reaction reversal (`pyramiding = 0`, same-direction pyramiding blocked).
- **Trades Generated:**
  - Standard OB Retest: `"Long"` / `"Short"` (SL at retest candle extreme, TP Limit at Target 2). Order comment: `[Long @ HH:MM IST]`.
  - ATH Reversal: `"ATH Short"` (SL at ATH high + buffer, TP Limit at 2nd low pullback). Order comment: `[ATH Short @ HH:MM IST]`.
  - ATL Reversal: `"ATL Long"` (SL at ATL low - buffer, TP Limit at 2nd high pullback). Order comment: `[ATL Long @ HH:MM IST]`.
  - Reversal Exits: Native `strategy.close()` with comments `[Rev Short @ HH:MM IST]`, `[Rev Long @ HH:MM IST]`, `[ATH Rev Short @ HH:MM IST]`, `[ATL Rev Long @ HH:MM IST]`.
- **Position Sizing:** 1% equity risk / 1% allocation per trade with lot-step quantization.
- **Session Filter:** Evaluated strictly in `Asia/Kolkata` (NSE 09:15-15:15 IST, MCX 18:15-23:00 IST) on Monday-Friday (`:23456`).
- **Execution Bar:** `process_orders_on_close = true` ensures execution at confirmed bar close price.
- **Stop Loss:** Native `strategy.exit(..., stop=sl_price)`. Order comment: `[SL @ HH:MM IST]`.
- **Take Profit:** Native `strategy.exit(..., limit=final_t2)`. Order comment: `[TP2 @ HH:MM IST]`.
- **MIS Square-Off:** Native `strategy.close_all()`. Order comment: `[MIS EOD Square-off @ HH:MM IST]`.
- **Alerts:** Automated alerts dispatched on fresh entries and opposite-OB reversal entries with explicit IST timestamps.

