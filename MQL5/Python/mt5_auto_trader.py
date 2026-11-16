#!/usr/bin/env python3
"""
mt5_auto_trader.py
Automated MT5 Position Sizing & Multi-Target Trade Execution Client.
Can run live via the 'MetaTrader5' Python library or in simulation mode.
"""

import sys
import math
from typing import Dict, List, Optional

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


class MT5AutoTradeManager:
    def __init__(self, simulation_mode: bool = False):
        self.simulation = simulation_mode or (not MT5_AVAILABLE)
        self.connected = False

    def connect(self, login: Optional[int] = None, password: Optional[str] = None, server: Optional[str] = None) -> bool:
        if self.simulation:
            print("[INFO] Running in SIMULATION / OFFLINE mode (MetaTrader5 package not active).")
            self.connected = True
            return True

        if not mt5.initialize():
            print(f"[ERROR] mt5.initialize() failed, error code = {mt5.last_error()}")
            return False

        if login and password and server:
            authorized = mt5.login(login=login, password=password, server=server)
            if not authorized:
                print(f"[ERROR] Failed to connect to trade account {login}, error: {mt5.last_error()}")
                return False

        self.connected = True
        account_info = mt5.account_info()
        print(f"[SUCCESS] Connected to MT5 Account: {account_info.login} ({account_info.name}) | Balance: ${account_info.balance:,.2f}")
        return True

    def disconnect(self):
        if not self.simulation and self.connected:
            mt5.shutdown()
        self.connected = False
        print("[INFO] Disconnected from MT5.")

    def get_symbol_specs(self, symbol: str) -> Dict:
        if self.simulation:
            # High-precision mock specs based on standard broker configurations
            is_forex = len(symbol) == 6 and symbol.isalpha()
            is_gold = "XAU" in symbol or "GOLD" in symbol
            is_crypto = "BTC" in symbol or "ETH" in symbol
            is_index = "30" in symbol or "100" in symbol or "500" in symbol

            digits = 5 if is_forex else (2 if (is_gold or is_crypto) else 1)
            point = 10 ** (-digits)
            ask = 1.08500 if is_forex else (2400.00 if is_gold else (65000.0 if is_crypto else 39500.0))
            bid = ask - (10 * point)

            return {
                "symbol": symbol,
                "digits": digits,
                "point": point,
                "tick_size": point,
                "tick_value_loss": 1.0 if is_forex else (1.0 if is_gold else (0.01 if is_crypto else 1.0)),
                "tick_value_profit": 1.0 if is_forex else (1.0 if is_gold else (0.01 if is_crypto else 1.0)),
                "volume_min": 0.01 if not is_index else 0.1,
                "volume_max": 100.0,
                "volume_step": 0.01 if not is_index else 0.1,
                "ask": ask,
                "bid": bid,
            }

        sym_info = mt5.symbol_info(symbol)
        if sym_info is None:
            raise ValueError(f"Symbol {symbol} not found in MT5.")

        if not sym_info.visible:
            mt5.symbol_select(symbol, True)

        tick = mt5.symbol_info_tick(symbol)
        return {
            "symbol": symbol,
            "digits": sym_info.digits,
            "point": sym_info.point,
            "tick_size": sym_info.trade_tick_size or sym_info.point,
            "tick_value_loss": sym_info.trade_tick_value_loss or 1.0,
            "tick_value_profit": sym_info.trade_tick_value_profit or 1.0,
            "volume_min": sym_info.volume_min,
            "volume_max": sym_info.volume_max,
            "volume_step": sym_info.volume_step,
            "ask": tick.ask,
            "bid": tick.bid,
        }

    def calculate_lot_size(
        self,
        symbol: str,
        direction: str,  # "BUY" or "SELL"
        risk_pct: float,
        stop_loss_pips: float,
        account_equity: Optional[float] = None
    ) -> Dict:
        """
        Calculates position size strictly conforming to account risk % and broker step rules.
        """
        specs = self.get_symbol_specs(symbol)

        if account_equity is None:
            if self.simulation:
                account_equity = 25000.0
            else:
                account_equity = mt5.account_info().equity

        entry_price = specs["ask"] if direction == "BUY" else specs["bid"]
        point = specs["point"]
        tick_size = specs["tick_size"]
        tick_val = specs["tick_value_loss"]
        vol_min = specs["volume_min"]
        vol_max = specs["volume_max"]
        vol_step = specs["volume_step"]

        sl_distance = stop_loss_pips * (point * 10.0)
        sl_price = (entry_price - sl_distance) if direction == "BUY" else (entry_price + sl_distance)
        sl_price = round(sl_price, specs["digits"])

        # Loss per 1.0 Lot
        ticks = sl_distance / tick_size
        loss_1_lot = ticks * tick_val

        # Cash Risk
        risk_cash = account_equity * (risk_pct / 100.0)
        raw_lots = risk_cash / loss_1_lot

        # Discretize to broker lot step
        decimals = max(0, int(round(-math.log10(vol_step))))
        steps = math.floor(raw_lots / vol_step + 1e-7)
        total_lots = round(steps * vol_step, decimals)

        # Clamping
        if total_lots < vol_min:
            total_lots = vol_min
        elif total_lots > vol_max:
            total_lots = vol_max

        actual_risk_cash = round(total_lots * loss_1_lot, 2)
        actual_risk_pct = round((actual_risk_cash / account_equity) * 100.0, 2)

        return {
            "symbol": symbol,
            "direction": direction,
            "equity": account_equity,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "sl_distance_pips": stop_loss_pips,
            "total_lots": total_lots,
            "loss_1_lot": round(loss_1_lot, 2),
            "planned_risk_cash": round(risk_cash, 2),
            "actual_risk_cash": actual_risk_cash,
            "actual_risk_pct": actual_risk_pct,
            "specs": specs
        }

    def place_trade_with_targets(
        self,
        symbol: str,
        direction: str,
        risk_pct: float,
        stop_loss_pips: float,
        targets: List[Dict],  # e.g. [{"rr": 1.5, "share": 50}, {"rr": 3.0, "share": 50}]
        magic_number: int = 8881001,
        comment: str = "PyAutoTrade"
    ) -> List[Dict]:
        """
        Calculates position size and submits multi-target orders to MT5.
        """
        sizing = self.calculate_lot_size(symbol, direction, risk_pct, stop_loss_pips)
        total_lots = sizing["total_lots"]
        specs = sizing["specs"]
        vol_step = specs["volume_step"]
        vol_min = specs["volume_min"]
        digits = specs["digits"]
        decimals = max(0, int(round(-math.log10(vol_step))))

        sl_pips = sizing["sl_distance_pips"]
        entry_price = sizing["entry_price"]
        sl_price = sizing["sl_price"]

        print(f"\n[CALCULATION COMPLETE] Symbol: {symbol} | Direction: {direction}")
        print(f"  -> Account Equity: ${sizing['equity']:,.2f}")
        print(f"  -> Total Volume: {total_lots} lots | SL: {sl_price} ({sl_pips} pips)")
        print(f"  -> Risk: ${sizing['actual_risk_cash']:,.2f} ({sizing['actual_risk_pct']}%)")

        # Split lots across targets
        share_sum = sum(t.get("share", 100.0 / len(targets)) for t in targets)
        allocated_sum = 0.0
        target_orders = []

        for i, t in enumerate(targets):
            share = t.get("share", 100.0 / len(targets))
            rr = t.get("rr", 2.0)
            raw_t_lot = total_lots * (share / share_sum)
            t_steps = math.floor(raw_t_lot / vol_step + 1e-7)
            t_lot = round(t_steps * vol_step, decimals)

            if t_lot < vol_min and total_lots >= vol_min and i == 0:
                t_lot = vol_min

            # Calculate Take Profit price
            tp_dist = (sl_pips * (specs["point"] * 10.0)) * rr
            tp_price = (entry_price + tp_dist) if direction == "BUY" else (entry_price - tp_dist)
            tp_price = round(tp_price, digits)

            target_orders.append({
                "target_index": i + 1,
                "volume": t_lot,
                "tp_price": tp_price,
                "rr": rr,
                "share": share
            })
            allocated_sum += t_lot

        # Remainder allocation to Target 1
        remainder = round(total_lots - allocated_sum, decimals)
        if abs(remainder) >= vol_step:
            target_orders[0]["volume"] = round(target_orders[0]["volume"] + remainder, decimals)

        # Execute orders
        results = []
        for t in target_orders:
            vol = t["volume"]
            tp = t["tp_price"]
            idx = t["target_index"]
            sub_comment = f"{comment}-T{idx}"

            if vol <= 0.0:
                continue

            if self.simulation:
                fake_ticket = 100000 + idx
                print(f"[SIMULATED ORDER EXECUTION] Target {idx}: {direction} {vol} lots @ {entry_price} | SL: {sl_price} | TP: {tp} (R:R 1:{t['rr']}) -> Ticket #{fake_ticket}")
                results.append({"ticket": fake_ticket, "target": idx, "volume": vol, "status": "SIMULATED_FILLED"})
            else:
                action_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": vol,
                    "type": action_type,
                    "price": entry_price,
                    "sl": sl_price,
                    "tp": tp,
                    "deviation": 10,
                    "magic": magic_number,
                    "comment": sub_comment,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                res = mt5.order_send(request)
                if res.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"[ERROR] Target {idx} failed: {res.comment} (code {res.retcode})")
                    results.append({"ticket": 0, "target": idx, "volume": vol, "status": f"FAILED_{res.retcode}"})
                else:
                    print(f"[LIVE ORDER FILLED] Target {idx}: Order #{res.order} Deal #{res.deal} | {vol} lots @ {res.price}")
                    results.append({"ticket": res.order, "target": idx, "volume": vol, "status": "FILLED"})

        return results


def main():
    print("=" * 70)
    print("MT5 AUTOMATED POSITION SIZING & TRADE EXECUTION DEMONSTRATION")
    print("=" * 70)

    manager = MT5AutoTradeManager(simulation_mode=True)
    manager.connect()

    # Scenario 1: Forex EURUSD BUY with 1% risk & 2 targets (50% at 1:1.5 RR, 50% at 1:3.0 RR)
    manager.place_trade_with_targets(
        symbol="EURUSD",
        direction="BUY",
        risk_pct=1.0,
        stop_loss_pips=25.0,
        targets=[
            {"rr": 1.5, "share": 50.0},
            {"rr": 3.0, "share": 50.0}
        ],
        comment="ScalpBreakout"
    )

    # Scenario 2: Gold XAUUSD SELL with 2% risk & 3 targets
    manager.place_trade_with_targets(
        symbol="XAUUSD",
        direction="SELL",
        risk_pct=2.0,
        stop_loss_pips=40.0,
        targets=[
            {"rr": 1.0, "share": 50.0},
            {"rr": 2.0, "share": 30.0},
            {"rr": 4.0, "share": 20.0}
        ],
        comment="GoldSwing"
    )

    manager.disconnect()
    print("=" * 70)
    print("AUTOMATION DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()

