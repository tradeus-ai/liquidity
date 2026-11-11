# Engineering Review: Entry Signals in `tradeus_liquidity_toolkit.pine`

## Feature Request

> When price touches an Order Block and then closes inside (or crosses) the **opposite side** FVG — with at least one candle difference — draw a Buy or Sell entry signal on the chart.
>
> - **Buy Signal:** Touches Bullish OB → candle closes inside/crosses Sell Side FVG
> - **Sell Signal:** Touches Bearish OB → candle closes inside/crosses Buy Side FVG

---

## Step 0: Scope Challenge

### What already exists that partially solves this?

The **strategy file** [`tradeus_reaction_strategy.pine`](file:///mnt/all/Trading/Courses/Xoduse/Liquidity/pine/tradeus_reaction_strategy.pine) already implements the *exact* OB-touch + opposite-FVG-close reaction pipeline with 14 decision gates (D1–D14), including candle separation, retest breach tracking, target discovery, and position management.

The **indicator file** [`tradeus_liquidity_toolkit.pine`](file:///mnt/all/Trading/Courses/Xoduse/Liquidity/pine/tradeus_liquidity_toolkit.pine) currently:
- Tracks OBs as **plain `box[]` arrays** (`bull_ob_boxes`, `bear_ob_boxes`) — just box objects, no metadata (no touch state, no bar tracking)
- Tracks FVGs as **`FvgItem[]` arrays** with `is_ifvg`, `ifvg_bar`, `is_closed` fields
- Has OB invalidation logic (lines 402–426) that removes OBs when candle closes beyond boundary
- Has FVG mitigation + iFVG conversion logic (lines 332–396)

### Gap: The indicator's OB data structure is too thin

The strategy has a rich `CandidateOB` UDT with `is_touched`, `touch_bar`, `last_touch_bar`, `touch_low`, `touch_high`. The indicator stores OBs as raw `box` objects with zero metadata. **This is the core problem.**

### Minimum viable change set

| # | Change | Touches |
|---|--------|---------|
| 1 | Create `ObItem` UDT (like `FvgItem`) with `bx`, `is_bullish`, `is_touched`, `touch_bar` | New type, ~6 lines |
| 2 | Replace `box[]` arrays with `ObItem[]` arrays | ~12 call sites |
| 3 | Add OB touch detection in the invalidation loop | ~20 lines per side |
| 4 | Add entry signal check: scan opposite FVGs for close-inside/crossing after touch | ~30 lines per side |
| 5 | Draw signal label + optional alert | ~10 lines |
| 6 | Input toggles + styling | ~8 lines |

**Total: ~100 lines added, 1 new UDT, 0 new files.** This is a clean single-file change.

> [!IMPORTANT]
> **Complexity check passes.** 1 file, 1 new UDT, well under the 8-file/2-class threshold.

---

## Section 1: Architecture

### Issue A1 — OB arrays store raw `box` objects, need metadata wrapping (P1 Blocker)

**Current state:** `bull_ob_boxes` and `bear_ob_boxes` are `box[]` arrays. Every OB operation (creation at lines 461–463, 506–508; invalidation at lines 402–426; trimming) works with raw `box` references.

**Problem:** You can't track "has this OB been touched?" or "which bar touched it?" without metadata. The `box.get_top()` / `box.get_bottom()` API only gives price boundaries.

**Recommendation:** Create an `ObItem` UDT mirroring `FvgItem`:

```pinescript
type ObItem
    box   bx
    bool  is_bullish
    bool  is_touched
    int   touch_bar      // bar_index when first touched
```

Replace `bull_ob_boxes` → `bull_ob_items` (`ObItem[]`), `bear_ob_boxes` → `bear_ob_items` (`ObItem[]`).

Update all 12 call sites: `array.push`, `array.get`, `array.remove`, `trim_ob_array`, and the invalidation loops.

### Issue A2 — FVG "opposite side" semantics need clarification (P1)

The user says:
- **Buy**: touch Bullish OB → close inside **Sell Side FVG**
- **Sell**: touch Bearish OB → close inside **Buy Side FVG**

In the indicator's naming convention:
- "Buy Side FVG" = Bullish FVG (`bull_fvg_items`) = gap above price = `curr_low > prev2_high`
- "Sell Side FVG" = Bearish FVG (`bear_fvg_items`) = gap below price = `curr_high < prev2_low`

So:
- **Buy signal:** Bullish OB touched → candle closes inside/crosses a **Bearish FVG** (`bear_fvg_items`)
- **Sell signal:** Bearish OB touched → candle closes inside/crosses a **Bullish FVG** (`bull_fvg_items`)

This maps to the strategy's existing logic. The "opposite side" is the FVG on the opposite direction from the OB.

### Issue A3 — Which FVG qualifies as "the opposite FVG"? (P1)

Two interpretation options:

| Option | Description | Behavior |
|--------|-------------|----------|
| **A: Any active opposite FVG** | Check if close enters *any* unmitigated opposite-side FVG in the array | More signals, less selective |
| **B: Most recent opposite FVG** | Only check the most recent unmitigated opposite-side FVG | Fewer signals, more institutional |

The strategy file uses Option B ("most recent active opposite FVG"). **Recommend Option A (any active)** for the indicator since it's a visualization tool, not a strategy. More signals = more learning opportunities on chart.

### Issue A4 — "Crosses" vs "Closes inside" — should crossing mean close beyond? (P2)

User says "closes inside opposite side FVG / crosses opposite side FVG". Two interpretations:

| Condition | Pine Logic (Bearish FVG, Buy signal) |
|-----------|--------------------------------------|
| Closes inside | `curr_close >= fvg_bottom and curr_close <= fvg_top` |
| Closes crossing (beyond) | `curr_close < fvg_bottom` (close punches through the entire FVG) |

The strategy file uses `curr_close >= fvg.bottom` for Buy (inside OR beyond), matching "loosened FVG inversion" (D4). **Recommend the same: `curr_close >= fvg_bottom` for Buy, `curr_close <= fvg_top` for Sell** — close anywhere inside or through the FVG counts.

### Issue A5 — iFVG status interaction (P2)

The indicator converts mitigated FVGs into iFVGs (lines 344–363, 377–396). Once a Bearish FVG is closed by a candle (close inside/above), it becomes a Bullish iFVG.

**Question:** Should the entry signal check run on FVGs that are already iFVGs? 

**Recommendation:** No — only check against FVGs that have NOT yet been inverted (`item.is_ifvg == false`). The entry signal itself IS the inversion event. If the FVG is already an iFVG, the reaction already happened on a prior bar.

---

## Section 2: Code Quality

### Issue C1 — Candle separation must be strictly enforced (P1 Blocker)

The user specifies "at least one candle difference." This means:

```
Bar N:   Candle touches OB (low <= ob_top for Bullish OB)
Bar N+1: Candle closes inside opposite FVG → SIGNAL ✅
Bar N:   Same candle touches OB AND closes inside FVG → NO SIGNAL ❌
```

This maps to the strategy's D6 rule: `bar_index > ob.touch_bar`.

**Implementation:** After recording `ob.touch_bar := bar_index` on OB touch, the signal check on the same bar is skipped. Signal check runs on `bar_index > ob.touch_bar`.

### Issue C2 — Signal deduplication (P2)

Without dedup, every bar that closes inside an active opposite FVG after OB touch will fire a signal. Need to mark the OB as "reacted" after the first signal:

```pinescript
if not ob.is_reacted and bar_index > ob.touch_bar
    // check opposite FVG
    ob.is_reacted := true  // prevent repeat signals
```

### Issue C3 — OB touch definition needs precision (P2)

For a **Bullish OB** (buy signal):
- Touch = candle `low <= ob_top` AND `close >= ob_bottom` (price enters OB zone without closing below it)

For a **Bearish OB** (sell signal):  
- Touch = candle `high >= ob_bottom` AND `close <= ob_top` (price enters OB zone without closing above it)

This matches the strategy's definition.

---

## Section 3: Tests / Verification

Since this is a TradingView indicator (not unit-testable), verification is visual:

### Test Scenarios

| # | Scenario | Expected |
|---|----------|----------|
| T1 | Bullish OB touched on bar N, bear FVG close on bar N+1 | Buy label ✅ |
| T2 | Bearish OB touched on bar N, bull FVG close on bar N+1 | Sell label ✅ |
| T3 | OB touched and FVG closed on same bar N | No signal ❌ |
| T4 | OB touched but no opposite FVG exists | No signal ❌ |
| T5 | OB already invalidated (close beyond boundary) | No signal ❌ |
| T6 | Multiple OBs touched, multiple FVGs available | Only first valid signal per OB |
| T7 | FVG already converted to iFVG before OB touch | No signal ❌ |

---

## Section 4: Performance

### Issue P1 — Loop complexity (P3 Low)

The signal check adds a nested loop: for each touched OB, scan opposite FVG array. With `max_fvgs=50` OBs and 50 FVGs, worst case is 50×50=2500 iterations per bar. Pine Script handles this easily (limit is ~500,000 loop iterations per bar).

### Issue P2 — Drawing object limits (P3 Low)

Entry signals use `label.new()`. The indicator header declares `max_labels_count=500`. The market structure engine, sweep engine, and FVGs already consume labels. Need to cap entry signal labels or ensure they stay within budget.

**Recommendation:** Add a `max_entry_signals` input (default 50) with FIFO trimming, same pattern as `trim_fvg_array`.

---

## Implementation Plan

### Task Breakdown

| # | Priority | Task | Lines |
|---|----------|------|-------|
| **T1** | P1 | Create `ObItem` UDT + migrate `bull_ob_boxes`/`bear_ob_boxes` to `ObItem[]` arrays | ~30 |
| **T2** | P1 | Add OB touch detection in invalidation/extension loops | ~20 |
| **T3** | P1 | Add entry signal scanner: for each touched OB, check opposite FVGs with candle separation | ~40 |
| **T4** | P1 | Draw entry signal labels (▲ Buy / ▼ Sell) with styling | ~15 |
| **T5** | P2 | Add module toggle, styling inputs, max signal count | ~15 |
| **T6** | P2 | Add alert conditions for entry signals | ~5 |

### Data Flow Diagram

```
                    ┌─────────────────────────┐
                    │  FVG Detection Engine    │
                    │  (bull_fvg_items,        │
                    │   bear_fvg_items)        │
                    └──────────┬──────────────┘
                               │
   ┌───────────────────────────┼───────────────────────────┐
   │                           │                           │
   ▼                           ▼                           ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ OB Detection │    │  FVG Mitigation  │    │ OB Invalidation  │
│ (creates     │    │  + iFVG Convert  │    │ + Touch Tracking │
│  ObItem)     │    │  (lines 332-396) │    │ (lines 402-426)  │
└──────┬───────┘    └──────────────────┘    └────────┬─────────┘
       │                                             │
       │              ┌─────────────────┐            │
       └──────────────► ENTRY SIGNAL    ◄────────────┘
                      │ SCANNER (NEW)   │
                      │                 │
                      │ For each touched│
                      │ OB: scan opp.   │
                      │ FVG array for   │
                      │ close-inside    │
                      │ (bar > touch)   │
                      └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │  Draw Signal    │
                      │  ▲ Buy / ▼ Sell │
                      │  label.new()    │
                      └─────────────────┘
```

### Key Design Decisions Needed

> [!WARNING]
> Before implementation, these 3 decisions need your input:

1. **Which FVGs qualify?** Any active opposite FVG (more signals) vs only the most recent one (fewer, more selective)?
2. **Signal visual style?** Triangle labels below/above bar (`label.style_triangleup` / `label.style_triangledown`) vs text labels ("BUY"/"SELL")?
3. **Should we also check iFVGs?** Or strictly only unconverted FVGs?
