# TradeUS SMC Toolkit

The **TradeUS SMC Toolkit** is a comprehensive, all-in-one Smart Money Concepts (SMC) indicator built for TradingView. It is designed to help traders identify structural liquidity, market shifts, and high-probability trading zones seamlessly.

This toolkit automatically maps complex market structures from higher timeframes down to execution timeframes, rendering clean, precise visual cues for Break of Structure (BOS), Change of Character (ChoCH), Inducement (#), and Supply/Demand zones.

## Features & Modules

The indicator is modular, allowing you to toggle each feature on or off based on your visual preference and trading strategy:

### 1. Market Structure Mapping (BOS / ChoCH / Inducement / IS)
The core of the toolkit automatically detects and labels critical structural points:
- **BOS (Break of Structure):** Confirmed when a candle closes beyond the previous confirmed structural high or low.
- **ChoCH (Change of Character):** Detects early trend reversals by marking the break of a major pullback low/high.
- **# (Inducement):** Identifies liquidity grabs before a true structural break occurs.
- **IS (Inducement Shift):** Tracks internal shifts when price wicks but fails to close above/below a key level.

### 2. Supply & Demand Zones
Automatically plots refined Supply and Demand zones based on unbroken swing points prior to structural breaks. These zones dynamically extend to the right and automatically disappear once mitigated by future price action.

### 3. Fair Value Gaps (FVG)
Detects unmitigated price imbalances in the market.
- **Bullish FVGs:** Highlighted in green, acting as potential support.
- **Bearish FVGs:** Highlighted in red, acting as potential resistance.
- FVGs dynamically mitigate and clear from the chart as price fills the gap.

### 4. SMC Pullbacks (ZigZag)
A dynamic zigzag line that maps out confirmed swing highs and swing lows. This visualizer helps you clearly see the current directional swings and pullbacks without the noise of minor price fluctuations.

### 5. Inside Bar Zones
Identifies and highlights periods of market consolidation (inside bars). The toolkit boxes these zones, projecting the high and low of the "mother bar" to help you spot potential breakout or liquidity sweep opportunities.

### 6. Buyer/Seller Candle Strength (Status Line)
A built-in histogram displayed on the status line and data window that calculates the relative strength of buyers versus sellers for every candle. This helps gauge momentum and pressure at key structural zones.

## How to Use

1. **Top-Down Analysis:** Start on a higher timeframe (e.g., Daily or 4H) to establish the overall market structure (BOS, ChoCH) and identify major Supply/Demand zones.
2. **Zone Refinement:** Toggle on FVGs and Inside Bars to see where liquidity is resting within or near those HTF zones.
3. **Execution:** Drop down to your execution timeframe (e.g., 15m or 1h) and look for a local ChoCH or Inducement sweep inside the HTF zone for a high-probability entry.

## Customization

All modules are highly customizable via the indicator settings:
- **Toggles:** Turn any of the 5 main modules on/off to keep your chart clean.
- **Colors & Styling:** Customize the colors, borders, and opacities for Inside Bars, FVGs, and Pullback lines.
- **FVG Limits:** Set a maximum number of historical FVGs to display, optimizing performance and chart clarity.

## Disclaimer

*This indicator is designed for educational and analytical purposes only. Smart Money Concepts and technical analysis do not guarantee future performance. Always use proper risk management and test any strategy or tool in a demo environment before trading with live capital.*
