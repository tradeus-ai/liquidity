# LIQUIDITY Finding

This project is all about finding liquidity from Higher timeframe to Lower timeframe analysis. Entering the market with high probability trade setup in lower timeframe based on market structure change. We use Python and its libraries to analyze the market and show results in higher timeframe and lower timeframe using any graphical tool which plots candlestick pattern

# Timeframes
Higher timeframe - Daily (for trend and demand/supply zones)
Lower timeframe - 15 mins (for entry) in Indian Markets and 1h in Forex Markets

# Data
we will use tradingview to fetch data from symbols present in @./Futures.csv

our scripts are limited to indian markets . We will use NSE for indian markets and we are using is OHLC data with volume & focusing only on Futures charts.

# Market structure in higher timeframe

Market structure consists of Inducement, BOS and Choch.
1. To find a market high or low, we need to draw a pullback structure.
2. After drawing a pullback structure, we will know swing highs/ lows.
3. If market breaks a swing low in uptrend and swing high in downtrend, then it is called Inducment.
4. Once Inducement occurs then market high / low is determined. if market candle closes above the market high/ market low. it is called as BOS (Break of Structure)
5. low / high from market high to Break of structure is called as ChoCH (Change of Character) and if ChoCH level goes slightly below / higher it is considered as broken.

# Zones
1. once market structure is confirmed, you would know the direction. it is either up trend / down trend.
2. Then we shall draw pullbacks to find swing highs / lows.
3. if it is in uptrends, swing lows are considered as demand zones. if it is in down trend, swing highs are considered as supply zones. These zones should be marked.


