# TFX Trade Manager EA & MQL5 Scripts Suite for MetaTrader 5

A production-grade, native MQL5 Trade Manager EA and automated risk calculation toolkit reverse-engineered and reconstructed from the commercial **TFX Trade Manager EA** architecture, incorporating industry-leading risk algorithms from EarnForex's open-source *Position Sizer*.

---

## 🌟 Key Features

### 1. Visual Drag-and-Drop Risk / Reward Chart Tool
- **Interactive On-Chart Lines:**
  - **Entry Line (Blue/Cyan):** Drag to adjust entry price. Automatically detects whether the order should be Market, Limit, or Stop.
  - **Stop Loss Line (Red):** Drag to adjust SL. Dynamically recalculates position size, cash loss, and risk % in real time.
  - **Multiple Take Profits (Green/Lime):** Up to 3 independent TP targets (TP1, TP2, TP3) with individual volume allocations and R:R ratios.
- **Follow Live Price Mode:** Automatically binds Entry line to live Ask (for Buy) or Bid (for Sell) with zero-lag bracket tracking for scalpers.
- **Lock Risk:Reward (`Lock R:R`):** Dragging the Stop Loss line automatically shifts all Take Profit lines proportionally to maintain your target Risk-to-Reward ratio!
- **On-Line Text Labels:** Live distance in points & pips, Risk/Reward ratio, and projected profit/loss displayed next to each line.

### 2. Multi-Asset Position Sizing Calculator
- Calculates exact lot sizes across:
  - **Forex Currencies** (EURUSD, USDJPY, GBPUSD, cross & inverse pairs)
  - **Metals & Commodities** (XAUUSD, XAGUSD, USOIL, UKOIL)
  - **Crypto Assets** (BTCUSD, ETHUSD)
  - **Stock Indices** (US30, NAS100, SPX500, NIFTY50, DAX40)
  - **Exchange Futures**
- Three flexible risk calculation modes:
  1. **Risk %:** Calculate lot size from account balance/equity % (e.g. 1.0%, 2.0%).
  2. **Risk Amount ($):** Calculate lot size from a fixed cash dollar amount (e.g. $100).
  3. **Fixed Lots:** Input lot size directly (reverse-computes risk $ and %).
- **Broker Constraint Normalization:**
  - Automatic lot step discretization: $\text{Lots} = \text{floor}(\text{RawLots} / \text{LotStep}) \times \text{LotStep}$.
  - Minimum lot clamping (`SYMBOL_VOLUME_MIN`) and maximum lot ceiling (`SYMBOL_VOLUME_MAX`).
  - Fractional remainder allocation to ensure multi-target sum strictly equals total position size.

### 3. Multi-Target Trade Splitting
- Divide any trade into **1, 2, or 3 Take Profit targets**.
- Configurable volume percentages per target (e.g., 50% TP1, 30% TP2, 20% TP3).
- Instant hotkey switching: `Ctrl + 1`, `Ctrl + 2`, `Ctrl + 3`.

### 4. Live Trades Management Panel (`Shift + M`)
- Real-time table of all active open positions.
- One-click bulk actions:
  - `Close All Trades`: Liquidates all open positions immediately.
  - `Close In Profit`: Closes only positions currently in profit.
  - `Close In Loss`: Closes only losing positions.
  - `Partial Close 50%`: Closes 50% of open volume across positions.
  - `Move All To Break-Even`: Sets SL of all positions to entry price (+ optional commission offset).

### 5. Account Exposure Panel (`Shift + X`)
- Real-time account risk overview: Balance, Equity, Used Margin, Free Margin, Margin Level %.
- Per-symbol net exposure breakdown (Total Long volume, Total Short volume, Net volume, Floating P&L).

### 6. Automated Trade Management
- **Auto Break-Even (BE):** Automatically shifts Stop Loss to entry price when trade moves $N$ points into profit.
- **Trailing Stop (TS):** Continuously trails Stop Loss behind price by defined points and step.

### 7. Keyboard Shortcuts (Hotkeys)
| Hotkey | Action |
| :--- | :--- |
| `Esc` | Show / Hide Visual Lines & close popup windows |
| `Shift + Esc` | Switch between BUY and SELL mode |
| `Ctrl + 1` | Set 1 Take Profit target |
| `Ctrl + 2` | Set 2 Take Profit targets |
| `Ctrl + 3` | Set 3 Take Profit targets |
| `Shift + E` | **Execute / Enter Order** |
| `Shift + M` | Toggle **Manage Trades** window |
| `Shift + X` | Toggle **Account Exposure** window |

---

## 📁 Repository Structure

```
MQL5/
├── Experts/
│   └── TFX_Trade_Manager/
│       ├── TFX_Trade_Manager_EA.mq5     # Main Expert Advisor
│       ├── TradeManagerDefines.mqh      # Constants, enums, structures, themes
│       ├── RiskCalculator.mqh           # Multi-asset risk & position sizing engine
│       ├── VisualTradeTool.mqh          # On-chart draggable lines & labels
│       ├── TradeManagerGUI.mqh          # On-chart GUI toolbar & popup windows
│       ├── OrderExecution.mqh           # CTrade multi-target execution, BE, & TS
│       └── HotkeyHandler.mqh            # Keyboard shortcut router
├── Scripts/
│   ├── Auto_Risk_Order_Placer.mq5       # Single-click instant risk calculator & order placer
│   ├── Close_All_Positions.mq5          # Instant close all positions script
│   ├── Close_Profitable_Positions.mq5   # Instant close winning positions script
│   ├── Move_To_Breakeven.mq5            # Move all positions to break-even script
│   └── Partial_Close_Positions.mq5      # Partial close open positions script
└── Python/
    ├── verify_position_sizing.py        # Mathematical unit tests across all asset classes
    └── mt5_auto_trader.py               # Python-to-MT5 automated position sizing & trade execution
```

---

## 🚀 Installation into MetaTrader 5

1. Open your MetaTrader 5 terminal.
2. In the top menu, click **File** -> **Open Data Folder**.
3. Navigate to `MQL5/`:
   - Copy `MQL5/Experts/TFX_Trade_Manager/` into your terminal's `MQL5/Experts/` folder.
   - Copy `MQL5/Scripts/` files into your terminal's `MQL5/Scripts/` folder.
4. In MT5, open the **Navigator** window (`Ctrl + N`), right-click on **Expert Advisors**, and click **Refresh**.
5. Ensure **Algo Trading** is enabled on the top toolbar:
   - Click the **Algo Trading** button (green play icon) in MT5.
   - In MT5 settings: **Tools** -> **Options** -> **Expert Advisors** -> Check **Allow Algo Trading**.
6. Drag `TFX_Trade_Manager_EA` onto any chart.

---

## 🧪 Verification & Automated Position Sizing

To verify the mathematical risk engine across Forex, Crypto, Indices, and Commodities, run:

```bash
python3 MQL5/Python/verify_position_sizing.py
```

To run the automated Python-to-MT5 trade placement client:

```bash
python3 MQL5/Python/mt5_auto_trader.py
```

