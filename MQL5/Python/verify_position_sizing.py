#!/usr/bin/env python3
"""
verify_position_sizing.py
Unit tests and verification of MQL5 Risk Calculator & Position Sizing Engine.
Validates multi-asset mathematics: Forex, Crypto, Indices, Commodities, and Futures.
"""

import math

def calculate_position_size(
    account_balance: float,
    risk_mode: str,          # "PERCENT" or "MONEY" or "FIXED_LOT"
    risk_value: float,       # e.g. 1.0 (for 1%) or 100.0 (for $100)
    entry_price: float,
    sl_price: float,
    tick_size: float,
    tick_value: float,
    vol_min: float = 0.01,
    vol_max: float = 100.0,
    vol_step: float = 0.01,
    num_targets: int = 2,
    shares: list = None
):
    """
    Exact Python reproduction of the MQL5 RiskCalculator algorithm.
    """
    if shares is None:
        shares = [50.0, 50.0] if num_targets == 2 else [100.0]

    # 1. Price distance
    sl_dist = abs(entry_price - sl_price)
    if sl_dist <= 0:
        raise ValueError("Entry price cannot equal Stop Loss price.")

    # 2. Loss per 1.0 lot
    ticks = sl_dist / tick_size
    loss_1_lot = ticks * tick_value
    if loss_1_lot <= 0:
        raise ValueError("Loss per 1.0 lot must be positive.")

    # 3. Determine cash risk amount
    if risk_mode == "PERCENT":
        risk_cash = account_balance * (risk_value / 100.0)
        raw_lots = risk_cash / loss_1_lot
    elif risk_mode == "MONEY":
        risk_cash = risk_value
        raw_lots = risk_cash / loss_1_lot
    elif risk_mode == "FIXED_LOT":
        raw_lots = risk_value
        risk_cash = raw_lots * loss_1_lot
    else:
        raise ValueError(f"Unknown risk mode: {risk_mode}")

    # 4. Normalize to broker step & clamp to min/max
    lot_step_decimals = max(0, int(round(-math.log10(vol_step))))
    steps = math.floor(raw_lots / vol_step + 1e-7)
    total_lots = round(steps * vol_step, lot_step_decimals)

    if total_lots < vol_min:
        total_lots = vol_min
    elif total_lots > vol_max:
        total_lots = vol_max

    # Actual realized risk after lot discretization
    actual_risk_cash = round(total_lots * loss_1_lot, 2)
    actual_risk_pct = round((actual_risk_cash / account_balance) * 100.0, 2)

    # 5. Multi-target lot splitting
    target_lots = []
    allocated_sum = 0.0
    share_sum = sum(shares[:num_targets])
    if share_sum <= 0:
        share_sum = 100.0

    for i in range(num_targets):
        target_share = shares[i] if i < len(shares) else (100.0 / num_targets)
        raw_t_lot = total_lots * (target_share / share_sum)
        t_steps = math.floor(raw_t_lot / vol_step + 1e-7)
        t_lot = round(t_steps * vol_step, lot_step_decimals)
        
        # Enforce minimum lot on first target if total >= min_lot
        if t_lot < vol_min and total_lots >= vol_min and i == 0:
            t_lot = vol_min

        target_lots.append(t_lot)
        allocated_sum += t_lot

    # Remainder allocation to Target 1
    rem = round(total_lots - allocated_sum, lot_step_decimals)
    if abs(rem) >= vol_step:
        target_lots[0] = round(target_lots[0] + rem, lot_step_decimals)

    return {
        "loss_1_lot": round(loss_1_lot, 4),
        "total_lots": total_lots,
        "actual_risk_cash": actual_risk_cash,
        "actual_risk_pct": actual_risk_pct,
        "target_lots": target_lots,
        "sum_targets": round(sum(target_lots), lot_step_decimals)
    }

def run_tests():
    print("=" * 70)
    print("RUNNING POSITION SIZING MATHEMATICAL VERIFICATION")
    print("=" * 70)

    test_cases = [
        {
            "name": "Forex EURUSD (1% Risk on $10,000, 30 pips SL)",
            "balance": 10000.0,
            "mode": "PERCENT",
            "val": 1.0,
            "entry": 1.08500,
            "sl": 1.08200,
            "tick_size": 0.00001,
            "tick_value": 1.0, # $1 per pip on 0.1 lot, $10 per pip on 1.0 lot -> tick_val = $1 per 0.00001 tick
            "vol_min": 0.01,
            "vol_max": 100.0,
            "vol_step": 0.01,
            "targets": 2,
            "shares": [60.0, 40.0]
        },
        {
            "name": "Forex USDJPY ($250 Fixed Cash Risk, 40 pips SL)",
            "balance": 25000.0,
            "mode": "MONEY",
            "val": 250.0,
            "entry": 155.000,
            "sl": 154.600,
            "tick_size": 0.001,
            "tick_value": 0.65, # Approx $0.65 per tick on USD account
            "vol_min": 0.01,
            "vol_max": 50.0,
            "vol_step": 0.01,
            "targets": 3,
            "shares": [50.0, 30.0, 20.0]
        },
        {
            "name": "Gold XAUUSD (2% Risk on $50,000, $5.00 SL distance)",
            "balance": 50000.0,
            "mode": "PERCENT",
            "val": 2.0,
            "entry": 2400.00,
            "sl": 2395.00,
            "tick_size": 0.01,
            "tick_value": 1.0, # 100 oz contract: 0.01 = $1.00
            "vol_min": 0.01,
            "vol_max": 50.0,
            "vol_step": 0.01,
            "targets": 2,
            "shares": [50.0, 50.0]
        },
        {
            "name": "Crypto BTCUSD (1.5% Risk on $20,000, $1,500 SL distance)",
            "balance": 20000.0,
            "mode": "PERCENT",
            "val": 1.5,
            "entry": 65000.0,
            "sl": 63500.0,
            "tick_size": 0.01,
            "tick_value": 0.01, # 1 BTC contract: $1.00 per $1.00 move
            "vol_min": 0.01,
            "vol_max": 20.0,
            "vol_step": 0.01,
            "targets": 2,
            "shares": [70.0, 30.0]
        },
        {
            "name": "Index US30 ($500 Risk on $100,000, 150 points SL)",
            "balance": 100000.0,
            "mode": "MONEY",
            "val": 500.0,
            "entry": 39500.0,
            "sl": 39350.0,
            "tick_size": 1.0,
            "tick_value": 1.0, # $1 per point on 1 lot
            "vol_min": 0.1,
            "vol_max": 200.0,
            "vol_step": 0.1,
            "targets": 3,
            "shares": [50.0, 30.0, 20.0]
        },
        {
            "name": "Micro Account Min-Lot Boundary (0.5% Risk on $100, 50 pips SL)",
            "balance": 100.0,
            "mode": "PERCENT",
            "val": 0.5,
            "entry": 1.10000,
            "sl": 1.09500,
            "tick_size": 0.00001,
            "tick_value": 1.0,
            "vol_min": 0.01,
            "vol_max": 10.0,
            "vol_step": 0.01,
            "targets": 2,
            "shares": [50.0, 50.0]
        }
    ]

    all_passed = True
    for idx, tc in enumerate(test_cases, 1):
        res = calculate_position_size(
            account_balance=tc["balance"],
            risk_mode=tc["mode"],
            risk_value=tc["val"],
            entry_price=tc["entry"],
            sl_price=tc["sl"],
            tick_size=tc["tick_size"],
            tick_value=tc["tick_value"],
            vol_min=tc["vol_min"],
            vol_max=tc["vol_max"],
            vol_step=tc["vol_step"],
            num_targets=tc["targets"],
            shares=tc["shares"]
        )

        # Verification check: sum of targets must strictly equal total_lots
        sum_ok = (res["sum_targets"] == res["total_lots"])
        # Min lot check
        min_ok = (res["total_lots"] >= tc["vol_min"])
        # Max lot check
        max_ok = (res["total_lots"] <= tc["vol_max"])

        status = "PASSED" if (sum_ok and min_ok and max_ok) else "FAILED"
        if status == "FAILED":
            all_passed = False

        print(f"Test {idx}: {tc['name']}")
        print(f"  -> Loss per 1.0 Lot: ${res['loss_1_lot']}")
        print(f"  -> Calculated Volume: {res['total_lots']} lots (Min: {tc['vol_min']}, Step: {tc['vol_step']})")
        print(f"  -> Actual Risk: ${res['actual_risk_cash']} ({res['actual_risk_pct']}%)")
        print(f"  -> Target Split: {res['target_lots']} (Sum: {res['sum_targets']})")
        print(f"  -> Status: [{status}]\n")

    print("=" * 70)
    if all_passed:
        print("ALL POSITION SIZING VERIFICATION TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME TESTS FAILED - CHECK OUTPUT ABOVE")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

