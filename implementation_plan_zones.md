# Supply & Demand Zones Fixes (Python)

This plan outlines the required fixes for `src/zone_service.py` to strictly adhere to the 8 rules provided for Supply & Demand zone extraction.

## 1. Uptrend / Downtrend IDM Zones (Rules 1, 3, 6, 7)
- **Current Behavior**: The script extracts zones for pullbacks strictly to the left of the inducement point. However, it completely **discards** any pullbacks that were mitigated *during* the leg's formation (before IDM was confirmed).
- **Proposed Fix**: The rule states "all pullbacks are zones". If a pullback was mitigated during the formation of the leg, we will still create a zone for it, but set its `end_time` to the exact candle where it was mitigated, adding it directly to historical zones so it is drawn up to its mitigation point. Unmitigated zones will be added to the active list.

## 2. Gap Rule (Rule 2)
- **Current Behavior**: If the candle immediately following the pullback gaps, the code completely redefines the zone to equal the gap itself (`zone_bottom = zone_top; zone_top = next_candle_low`).
- **Proposed Fix**: The rule states "zone ends when gap between candle ends". This implies the zone's base (pullback low) should remain intact, but the *top* of the zone should extend to the gap's boundary (the next candle's low). I will adjust the logic so the zone is `[pullback low, next_candle_low]` instead of just the gap.

## 3. Clear on BOS/ChoCH (Rule 4)
- **Current Behavior**: The script correctly calls `clear_on_bos` and `clear_on_choch` which sets the `end_time` of all active zones and moves them to historical zones. This correctly terminates the zones visually at the ChoCH/BOS line. No changes needed to the clearance logic itself.

## 4. Inducement Shift (Rule 5)
- **Current Behavior**: When an Inducement Shift occurs, the script correctly scans for pullbacks strictly between the old high and the new high, and to the left of the new IS pullback.
- **Proposed Fix**: Ensure that the rule "draw zones on the left side of inducement shift" correctly includes all pullbacks to the left of the IS. The current logic is theoretically sound, but will be updated to match the new mitigation logic from Rule 1.

## 5. Show Only Active Zones (Rule 8)
- **Current Behavior**: `get_all_zones()` returns `historical_zones`. In Python UI drawing, historical zones represent zones that were active at some point and have a start/end time.
- **Proposed Fix**: To "show only active zones", the definition might mean we completely hide mitigated zones, OR it means we only show zones that were active during the current leg (ChoCH to BOS). I will filter out any zones that don't belong to the current structural cycle, ensuring we only return zones from the active trend leg (ChoCH to BOS after IDM).

## Open Questions for User
> [!IMPORTANT]
> 1. **Gap Rule**: When you say "zone ends when gap between candle ends", do you mean the zone's top boundary should be the gap's edge, but the bottom boundary remains the pullback low?
> 2. **Rule 8**: When you say "show only active zones... from Choch to BOS", do you want to completely HIDE zones that were mitigated (touched by price), or should mitigated zones still be drawn but stop at the candle where they were mitigated?
> 3. **Mitigated Pullbacks**: If a pullback is touched by price *before* the Inducement is even confirmed, should we draw a zone for it that immediately ends, or completely ignore it?

