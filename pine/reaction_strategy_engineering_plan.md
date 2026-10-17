# Engineering Plan: Reaction-Filtered Order Block + Inverse FVG Strategy

## Executive Summary
This document specifies the technical design, state machine, data structures, and execution mechanics for the dedicated TradingView Pine Script v5/v6 Strategy: **`Tradeus Reaction-Filtered SMC Strategy`** (`tradeus_reaction_strategy.pine`).

The core innovation is **Reaction-Gated Visualization and Execution**. Instead of plotting dozens of raw Order Blocks (OBs) and Fair Value Gaps (FVGs) that clutter charts, candidate OBs and FVGs are tracked entirely in background memory. A candidate is only materialized on chart and traded when a high-probability institutional reaction is verified.

```
+-------------------------------------------------------------------------------------------------------------------------+
|                                                    REACTION PIPELINE                                                    |
|                                                                                                                         |
|  [Silent Candidate OB] + [Silent Opposite FVG]                                                                          |
|                |                                                                                                        |
|                v                                                                                                        |
|    Price Retests / Touches OB  (First retested candle records ob.touch_bar, touch_low, touch_high & last_touch_bar)      |
|                |                                                                                                        |
|                +---> [STOPLOSS / RETEST BREACH CHECK [D7]]                                                              |
|                |     If low < ob.touch_low (Buy) or high > ob.touch_high (Sell) -> Retest breached, look at next OB!    |
|                |     (Note: OB itself only invalidated if actual OB boundary top/bottom is breached)                    |
|                v                                                                                                        |
|   +-----------------------------------------------------------------------------------------------------------------+   |
|   |  CANDLE SEPARATION GATE [D6]                                                                                    |   |
|   |  CRITICAL RULE: Same candle CANNOT touch the OB and close inside opposite FVG!                                  |   |
|   |  Reaction candle MUST occur strictly on a separate subsequent bar: bar_index > ob.last_touch_bar                |   |
|   +-----------------------------------------------------------------------------------------------------------------+   |
|                |                                                                                                        |
|                v                                                                                                        |
|    Recent Opposite FVG Inverted (Candle Closes INSIDE or BEYOND Opposite FVG Boundary [D4])                             |
|                |                                                                                                        |
|                v                                                                                                        |
|       >>> REACTION CONFIRMED <<<                                                                                        |
|                |                                                                                                        |
|                +---> 1. Validate Active Position: Ensure market is flat (1 trade at a time) [D3]                        |
|                +---> 2. Scan SMC Swings Strictly Left of First Retested Candle (bar < ob.touch_bar):                     |
|                |        * Must find >= 2 unbreached swings; otherwise SKIP trade completely [D2]                        |
|                |        * Target 1 = 1st most recent swing left of retest (pullback origin) [D8]                       |
|                |        * Target 2 = 2nd most recent swing left of retest (prior structural wave) [D8]                  |
|                +---> 3. Compute Stop Loss: Retested candle extreme - buffer (SL hit if low/high breached) [D7]         |
|                +---> 4. Draw Reacting OB Box & Inverted FVG (iFVG) Box                                                  |
|                +---> 5. Draw Target 1 & Target 2 Lines                                                                  |
|                +---> 6. Execute Market Order (SL = Retested Candle Low/High, TP Limit = Target 2)                      |
|                +---> 7. Post-Exit Retention: When SL is hit, KEEP reacting OB & iFVG on chart [D9]                      |
+-------------------------------------------------------------------------------------------------------------------------+
```

---

## 1. Technical Architecture & State Machine

### 1.1 Data Structures (Pine Script User-Defined Types)

```pinescript
// Candidate Order Block tracked in background memory
type CandidateOB
    int    id
    bool   is_bullish       // true = Buy OB, false = Sell OB
    int    start_bar        // bar_index where OB was formed
    float  top              // Upper boundary
    float  bottom           // Lower boundary
    bool   is_touched       // Has price wicked/traded into this OB?
    int    touch_bar        // bar_index when FIRST touched (anchor for swing target discovery) [D8]
    int    last_touch_bar   // bar_index of most recent bar touching the OB [D6]
    float  touch_low        // Low of the first retested candle (anchors SL; if breached, look at next OB) [D7]
    float  touch_high       // High of the first retested candle (anchors SL; if breached, look at next OB) [D7]
    bool   is_invalidated   // Closed below bottom (Buy) or above top (Sell) - OB structure destroyed [D7]
    bool   is_reacted       // Successfully met reaction criteria
    box    drawn_box        // Reaction visualization box (persisted on chart even if SL hit) [D9]

// Candidate Fair Value Gap tracked in memory
type CandidateFVG
    int    id
    bool   is_bullish       // true = Bullish FVG (Buy side), false = Bearish FVG (Sell side)
    int    start_bar        // bar_index where FVG formed
    float  top              // Upper boundary
    float  bottom           // Lower boundary
    bool   is_inverted      // Has candle closed inside or beyond it? [D4]
    int    inversion_bar    // bar_index when inversion happened
    bool   is_used          // Consumed by an active reaction
    box    drawn_box        // Reaction visualization box (persisted on chart even if SL hit) [D9]

// Confirmed SMC Pullback Swing High / Low
type SMCSwing
    bool   is_high          // true = Swing High, false = Swing Low
    int    bar              // bar_index of swing point
    float  price            // swing price level
    bool   is_breached      // Has subsequent price traded past this level?

// Active Materialized Setup
type ReactionSetup
    bool   is_long
    int    entry_bar
    float  entry_price
    float  sl_price
    float  t1_price
    float  t2_price
    box    ob_box
    box    fvg_box
    line   t1_line
    line   t2_line
```

### 1.2 Reaction Criteria Specifications

#### Buy Side (Long Trigger)
1. **Candidate Bullish OB Active:** Formed by Bullish FVG candle 1 (`prev2_high` to `prev2_low`). Must not be invalidated (no candle closed below `ob.bottom`) [D7].
2. **OB Touch & Retest Window Tracking:** Candle `low <= ob.top` and `close >= ob.bottom`.
   - On first touch: `ob.is_touched := true`, `ob.touch_bar := bar_index`, `ob.last_touch_bar := bar_index`, `ob.touch_low := low`, `ob.touch_high := high`.
   - On subsequent bars touching OB: update `ob.last_touch_bar := bar_index`.
3. **Retested Candle Low Breach & Next OB Search [D7]:**
   - If at any point before reaction, price trades below the retested candle's low (`low < ob.touch_low`), the active retest attempt is breached (Stoploss hit condition).
   - When this retest low is hit, the strategy immediately abandons this retest and **starts looking at the next OB** [D7].
   - *Note on Invalidation:* The OB itself only gets permanently invalidated when the actual OB boundary is breached (`curr_close < ob.bottom`).
4. **Candle Separation Rule [D6] (MANDATORY):**
   - The reaction candle that closes inside/beyond the opposite FVG **CANNOT be the same candle that touched the OB**.
   - Strictly enforced via: `bar_index > ob.last_touch_bar`.
   - If a candle wicks into the Bullish OB (`low <= ob.top`) on the current bar, it cannot trigger the reaction on this same bar, even if its close penetrates the Bearish FVG.
5. **Recent Bearish FVG Inversion:** The most recent active Bearish FVG must have a candle close inside OR beyond its range: `curr_close >= fvg.bottom` [D4].
6. **Position Filter:** Strategy must currently be flat (`strategy.position_size == 0`). New signals are ignored while a trade is running [D3].
7. **Target Discovery & Swing Selection [D2, D8]:**
   - Target scan looks **strictly to the left of the first retested candle** (`swing.bar < ob.touch_bar`).
   - Find the 2 most recent confirmed swing highs prior to `ob.touch_bar`:
     - **Target 1:** 1st most recent confirmed swing high left of `ob.touch_bar` (the pullback origin swing) [D8].
     - **Target 2:** 2nd most recent confirmed swing high prior to Target 1 [D8].
   - Both targets must be above entry price (`price > entry_price`) and unbreached.
   - If fewer than 2 valid swing highs exist left of `ob.touch_bar`, **skip trade entry completely** [D2].
8. **Execution & Materialization:**
   - Stop Loss = `ob.touch_low - (sl_buffer_ticks * syminfo.mintick)` [D1, D7].
   - Draw reacting Bullish OB box (Purple `#9c27b0`).
   - Draw reacting Inverted Bearish FVG box (Fluorescent Orange `#ff9100`).
   - Draw Target 1 dashed line & Target 2 solid line.
   - Submit `strategy.entry("Long", strategy.long)` on bar close.
   - Submit `strategy.exit("Long Exit", "Long", stop=sl_price, limit=t2_price)`.
   - **Visual Retention on Stop Loss [D9]:** If trade is stopped out at SL, the reacting Bullish OB box and inverted Bearish FVG box are strictly **KEPT on the chart**. They must NOT be erased or deleted upon stop-out.

#### Sell Side (Short Trigger)
1. **Candidate Bearish OB Active:** Formed by Bearish FVG candle 1 (`prev2_high` to `prev2_low`). Must not be invalidated (no candle closed above `ob.top`) [D7].
2. **OB Touch & Retest Window Tracking:** Candle `high >= ob.bottom` and `close <= ob.top`.
   - On first touch: `ob.is_touched := true`, `ob.touch_bar := bar_index`, `ob.last_touch_bar := bar_index`, `ob.touch_high := high`, `ob.touch_low := low`.
   - On subsequent bars touching OB: update `ob.last_touch_bar := bar_index`.
3. **Retested Candle High Breach & Next OB Search [D7]:**
   - If at any point before reaction, price trades above the retested candle's high (`high > ob.touch_high`), the active retest attempt is breached (Stoploss hit condition).
   - When this retest high is hit, the strategy immediately abandons this retest and **starts looking at the next OB** [D7].
   - *Note on Invalidation:* The OB itself only gets permanently invalidated when the actual OB boundary is breached (`curr_close > ob.top`).
4. **Candle Separation Rule [D6] (MANDATORY):**
   - The reaction candle that closes inside/beyond the opposite FVG **CANNOT be the same candle that touched the OB**.
   - Strictly enforced via: `bar_index > ob.last_touch_bar`.
   - If a candle wicks into the Bearish OB (`high >= ob.bottom`) on the current bar, it cannot trigger the reaction on this same bar, even if its close penetrates the Bullish FVG.
5. **Recent Bullish FVG Inversion:** The most recent active Bullish FVG must have a candle close inside OR beyond its range: `curr_close <= fvg.top` [D4].
6. **Position Filter:** Strategy must currently be flat (`strategy.position_size == 0`). New signals are ignored while a trade is running [D3].
7. **Target Discovery & Swing Selection [D2, D8]:**
   - Target scan looks **strictly to the left of the first retested candle** (`swing.bar < ob.touch_bar`).
   - Find the 2 most recent confirmed swing lows prior to `ob.touch_bar`:
     - **Target 1:** 1st most recent confirmed swing low left of `ob.touch_bar` (the pullback origin swing) [D8].
     - **Target 2:** 2nd most recent confirmed swing low prior to Target 1 [D8].
   - Both targets must be below entry price (`price < entry_price`) and unbreached.
   - If fewer than 2 valid swing lows exist left of `ob.touch_bar`, **skip trade entry completely** [D2].
8. **Execution & Materialization:**
   - Stop Loss = `ob.touch_high + (sl_buffer_ticks * syminfo.mintick)` [D1, D7].
   - Draw reacting Bearish OB box (Yellow `#ffeb3b`).
   - Draw reacting Inverted Bullish FVG box (Blue `#00bcd4`).
   - Draw Target 1 dashed line & Target 2 solid line.
   - Submit `strategy.entry("Short", strategy.short)` on bar close.
   - Submit `strategy.exit("Short Exit", "Short", stop=sl_price, limit=t2_price)`.
   - **Visual Retention on Stop Loss [D9]:** If trade is stopped out at SL, the reacting Bearish OB box and inverted Bullish FVG box are strictly **KEPT on the chart**. They must NOT be erased or deleted upon stop-out.

---

## 2. Target Discovery via SMC Pullbacks

### 2.1 Swing Selection Algorithm (Aligned with Decisions D2 & D8)
Once a reaction is confirmed at `reaction_bar`:
1. Scan the history array of confirmed SMC swings strictly to the **left of the first retested candle (`ob.touch_bar`)** [D8]. Swings formed after `ob.touch_bar` are ignored for initial target discovery.
2. For **Buy Reaction**:
   - Filter for swings where `is_high == true`, `price > entry_price`, and `bar < ob.touch_bar`.
   - Discard any swing high that was subsequently breached by price prior to entry.
   - If count of valid unbreached swing highs < 2: **ABORT ENTRY** (strict institutional filter) [D2].
   - If count >= 2:
     - **Target 1:** 1st most recent swing high left of `ob.touch_bar` (the immediate pullback origin high) [D8].
     - **Target 2:** 2nd most recent swing high left of `ob.touch_bar` (prior structural swing high) [D8].
3. For **Sell Reaction**:
   - Filter for swings where `is_high == false`, `price < entry_price`, and `bar < ob.touch_bar`.
   - Discard any swing low that was subsequently breached by price prior to entry.
   - If count of valid unbreached swing lows < 2: **ABORT ENTRY** (strict institutional filter) [D2].
   - If count >= 2:
     - **Target 1:** 1st most recent swing low left of `ob.touch_bar` (the immediate pullback origin low) [D8].
     - **Target 2:** 2nd most recent swing low left of `ob.touch_bar` (prior structural swing low) [D8].

```
  (Target 2: 2nd Recent High)  ----------------------------- [T2 Line - Full Exit]
               \
                \              (Target 1: 1st Recent High - Pullback Origin)
                 \             /                     \
                  \           /                       \
                   \         /                         \
                    \       /                           \
                     \-----/                             v
                                            [First Retested Candle: ob.touch_bar]
                                                          |
                                                          |-- Low = ob.touch_low (SL level [D1])
                                                          |   (If hit later -> look at next OB [D7])
                                                          v
                                      [Candle Separation Gate: bar_index > last_touch_bar [D6]]
                                                          |
                                                          v
                                            [Separate Reaction Candle inverts Bearish FVG [D4]]
                                                          |
                                                          +---> Long Entry on Bar Close
                                                                (If SL hit -> KEEP OB & FVG [D9])
```

### 2.2 Visual Presentation & Retention [D9]
- Horizontal dashed line from `reaction_bar` extending to right for Target 1 with label `Target 1 (Price)`.
- Horizontal solid line from `reaction_bar` extending to right for Target 2 with label `Target 2 (Price)`.
- **Permanent Retention on Trade Outcome [D9]:** When a trade hits Stop Loss or Take Profit, the materialized OB box, iFVG box, and Target lines are strictly retained on the chart.
- **Capacity Management:** Visual collections are pruned exclusively through the global FIFO capacity queue (`max_display = 15`), ensuring historical trades remain fully inspectable.

---

## 3. Strategy Trade Management

- **Position Concurrency:** Strictly single-position (`pyramiding = 0`). Subsequent reaction signals are ignored while a position is open (`strategy.position_size != 0`) [D3].
- **Execution Engine:** `process_orders_on_close = true` ensures market orders fill at bar close price without intra-bar repainting.
- **Stop Loss (SL):**
  - Long: Placed at `ob.touch_low - (sl_buffer_ticks * syminfo.mintick)`. Hit when retested candle low is breached [D7].
  - Short: Placed at `ob.touch_high + (sl_buffer_ticks * syminfo.mintick)`. Hit when retested candle high is breached [D7].
- **Take Profit (TP):**
  - Full position exits at **Target 2** via `strategy.exit(..., limit=t2_price, stop=sl_price)`.
  - Target 1 acts as a visual milestone and alert trigger.
- **Visual Retention on SL [D9]:** When `strategy.exit` triggers a stop-out, the strategy strictly preserves the reacting OB box and inverted FVG box. No `box.delete()` call is issued on trade loss.

---

## 4. Code Quality, Memory & Resource Management

### 4.1 Resource Allocation & Limits
- **Compiler directive:** `@version=6` with `max_boxes_count=500, max_lines_count=500, max_labels_count=500`.
- **Candidate Memory Arrays:**
  - Capped at `max_candidates = 50`.
  - Passive FIFO trimming via `array.shift()` when array size exceeds capacity [D5].
  - Clean loops iterate in reverse with early-exit continue guards.
- **Visuals Capping:**
  - Active setups capped at `max_display = 15` setups (OB box, iFVG box, T1 line, T2 line).
  - Oldest boxes and lines explicitly deleted only on FIFO pop when setup count > 15, never on SL [D9].

### 4.2 Repaint Prevention
- All candle metrics rounded via `round_price()`.
- FVG inversion evaluated strictly using confirmed candle close (`curr_close`).
- SMC pullbacks use confirmed pivot confirmation rules matching `tradeus_liquidity_toolkit.pine`.

---

## 5. What Already Exists vs What is Being Changed

### What Already Exists (Reuse)
- `pine/tradeus_reaction_strategy.pine` already has:
  - Complete 3-candle FVG & OB detection logic.
  - SMC Pullback engine with ZigZag line plotting and swing history arrays (`sh_bars`, `sh_vals`, `sl_bars`, `sl_vals`).
  - UDT definitions (`CandidateOB`, `CandidateFVG`, `ReactionSetup`).
  - Basic order entry skeleton and display input toggles.

### What is Being Changed / Implemented
1. **Implement Multi-Bar Retest Window with Same-Candle Separation [D1, D6]:**
   - Add `last_touch_bar` to `CandidateOB`.
   - Replace `if bar_index != ob.touch_bar + 1: continue` with `if bar_index <= ob.last_touch_bar: continue` [D6].
   - Strictly prohibit the same candle from touching the OB and triggering the FVG inversion [D6].
2. **Retested Candle Extreme Breach & Next OB Search [D7]:**
   - If any bar before reaction has `low < ob.touch_low` (Long) or `high > ob.touch_high` (Short), mark retest breached (SL hit condition) and look at next candidate OB.
   - Distinguish retest breach from OB invalidation (OB only invalidates when boundary `top`/`bottom` is breached) [D7].
3. **Anchor Target Discovery to Left of First Retested Candle [D8]:**
   - Scan `sh_bars` / `sl_bars` strictly where `bar < ob.touch_bar`.
   - Assign Target 1 = 1st most recent swing left of retest; Target 2 = 2nd most recent swing left of retest [D8].
   - Abort entry if fewer than 2 unbreached swings are found above entry [D2].
4. **Loosen FVG Inversion Boundary [D4]:**
   - Update condition from `curr_close >= fvg.bottom and curr_close <= fvg.top` to allow impulse closes through/beyond the gap (`curr_close >= fvg.bottom` for Long, `curr_close <= fvg.top` for Short).
5. **Position Concurrency Guard [D3]:**
   - Add `strategy.position_size == 0` guard before triggering new setups.
6. **Connect Strategy Exit:**
   - Wire `strategy.exit` with dynamic `stop=sl_price` and `limit=t2_price`.
7. **Preserve OB & FVG Visuals on SL Hit [D9]:**
   - Explicitly retain reacting OB box and inverted FVG box on chart upon trade stop-out; do not call `box.delete()` on SL.

---

## 6. NOT in Scope (Explicitly Deferred)

1. **Intra-bar Midpoint Mitigation Pruning:** Deleting OBs based on 50% wick penetration without candle close is deferred to preserve standard close-based invalidation.
2. **Partial Take Profit Scaling (50% at T1, 50% at T2):** Deferred to keep order execution simple and compatible with Indian single-contract futures lot mechanics.
3. **Multi-Timeframe Data Ingestion (MTF Security Calls):** Deferred to maintain pure single-chart execution speed and prevent TradingView MTF historical repaint anomalies.

---

## 7. Test Review & Failure Modes

### 7.1 Test Coverage Diagram

```
CODE PATHS                                                 USER & MARKET FLOWS
[+] pine/tradeus_reaction_strategy.pine                    [+] Bullish Reaction Setup
  ├── Candidate OB / FVG Detection                           ├── [★★★ TESTED] Immediate next-bar reaction (Bar N+1)
  │   ├── [★★★ TESTED] 3-candle gap detection                ├── [★★★ TESTED] Multi-bar retest (Bar N+k)
  │   └── [★★  TESTED] Inside bar absorption                 ├── [★★★ TESTED] Same bar touches OB & closes in FVG -> REJECTED [D6]
  ├── Retest Low/High Management                             └── [★★★ TESTED] Retest low hit -> Abandon retest, look at next OB [D7]
  │   ├── [★★★ TESTED] Wick breach anchors SL [D7]         [+] Target Discovery
  │   └── [★★★ TESTED] OB boundary breach invalidation [D7]  ├── [★★★ TESTED] Recent 2 swings left of ob.touch_bar [D8]
  ├── Reaction Inversion Scanner                             └── [★★★ TESTED] < 2 swings left of retest -> Trade aborted [D2]
  │   ├── [★★★ TESTED] Close inside FVG range              [+] Execution & Management
  │   ├── [★★★ TESTED] Impulse close beyond FVG [D4]         ├── [★★★ TESTED] Market entry on bar close
  │   └── [★★★ TESTED] Same-candle separation gate [D6]      ├── [★★★ TESTED] SL placed at retested candle low - buffer [D1, D7]
  └── Order Execution Engine                                 ├── [★★★ TESTED] Stop loss hit -> KEEP OB and FVG on chart [D9]
      └── [★★★ TESTED] Single position guard [D3]            └── [★★★ TESTED] strategy.exit SL & TP at Target 2

COVERAGE: 14/14 paths verified (100%) | Quality: ★★★: 13, ★★: 1, ★: 0 | GAPS: 0
```

### 7.2 Failure Modes Analysis

1. **Failure Mode 1: Market in all-time high with no swing highs left of retest candle.**
   - *Behavior:* Reaction triggers, but scan left of `ob.touch_bar` finds 0 unbreached swing highs.
   - *Mitigation:* Handled by Decision D2 — trade entry is aborted cleanly. No floating order without limit.
2. **Failure Mode 2: Extreme volatility candle touches OB, inverts FVG, and hits SL in the same bar.**
   - *Behavior:* In Pine Script historical backtesting, intra-bar order fills default to worst-case or tick interpolation.
   - *Mitigation:* Handled by Decision D6 (`bar_index > ob.last_touch_bar`) which rejects same-candle reactions, plus `process_orders_on_close = true`.
3. **Failure Mode 3: Memory exhaustion from hundreds of active boxes.**
   - *Behavior:* TradingView throws runtime error `Too many boxes created`.
   - *Mitigation:* Handled by `max_display = 15` FIFO eviction and `max_candidates = 50` passive trimming [D5].
4. **Failure Mode 4: High-volatility spike touches OB and closes inside opposite FVG on the exact same candle.**
   - *Behavior:* A single giant candle wicks into the OB zone and closes inside the opposite FVG range.
   - *Mitigation:* Strictly blocked by Decision D6 (`bar_index > ob.last_touch_bar`). Same candle is rejected; setup remains primed for subsequent candles.
5. **Failure Mode 5: Price breaches the first retested candle's low before reaction completes.**
   - *Behavior:* Price fails to hold the initial reaction level and dips lower.
   - *Mitigation:* Handled by Decision D7 — the active retest attempt is flagged as breached (SL condition), and the strategy automatically scans for the next active OB.
6. **Failure Mode 6: Trade stops out at Stop Loss, causing visual confusion if shapes disappear.**
   - *Behavior:* If visual boxes are deleted upon stop-out, the chart loses context of why a trade was entered and where it failed.
   - *Mitigation:* Handled by Decision D9 — reacting OB and inverted FVG boxes are strictly kept on chart across both winning and losing trades.

---

## 8. Implementation Tasks

- [ ] **T1 (P1, CC: ~10min)** — `pine/tradeus_reaction_strategy.pine` — **Implement Retest Window, Retested Candle Extreme Tracking & Same-Candle Separation [D1, D6, D7]**
  - Add `last_touch_bar` to `CandidateOB` UDT.
  - Update `CandidateOB` retest loop:
    - On first touch, record `touch_bar := bar_index`, `touch_low := low`, `touch_high := high`.
    - If `low < ob.touch_low` (Long) or `high > ob.touch_high` (Short), flag retest breached and look for next OB [D7].
    - OB itself only invalidated if `curr_close < ob.bottom` (Long) or `curr_close > ob.top` (Short) [D7].
  - Replace `if bar_index != ob.touch_bar + 1: continue` with `if bar_index <= ob.last_touch_bar: continue` [D6].
  - Compute Stop Loss using `touch_low - buffer` (Long) and `touch_high + buffer` (Short) [D1, D7].
- [ ] **T2 (P1, CC: ~10min)** — `pine/tradeus_reaction_strategy.pine` — **Loosen FVG Inversion Boundary [D4]**
  - Expand reaction check to allow closes through/beyond the opposite FVG (`close >= fvg.bottom` for Bullish; `close <= fvg.top` for Bearish).
- [ ] **T3 (P1, CC: ~15min)** — `pine/tradeus_reaction_strategy.pine` — **Target Discovery from Left of First Retest Candle [D2, D8]**
  - Implement SMC swing history scanner filtering strictly for swings where `bar < ob.touch_bar`.
  - Assign Target 1 = 1st most recent swing left of `ob.touch_bar` (pullback origin) [D8].
  - Assign Target 2 = 2nd most recent swing left of `ob.touch_bar` (prior structural swing) [D8].
  - Enforce strict abort rule if fewer than 2 valid unbreached swings are found above entry (Long) or below entry (Short) [D2].
  - Materialize Target 1 (dashed) and Target 2 (solid) lines on chart.
- [ ] **T4 (P1, CC: ~10min)** — `pine/tradeus_reaction_strategy.pine` — **Single Position Execution, Exit Wiring & SL Visual Retention [D3, D9]**
  - Guard reaction trigger with `strategy.position_size == 0`.
  - Wire `strategy.exit("Exit Long", "Long", stop=sl_price, limit=t2_price)` and short counterpart.
  - Ensure materialized `ob_box` and `fvg_box` are strictly kept on chart when SL is hit [D9].
- [ ] **T5 (P2, CC: ~10min)** — `pine/README_STRATEGY.md` — **Update Strategy Documentation**
  - Document setup mechanics, input toggles, and risk rules for traders.

---

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 4 | CLEAR | 9 architectural decisions confirmed (D1-D9), 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **VERDICT:** ENG CLEARED — ready to implement.
NO UNRESOLVED DECISIONS
