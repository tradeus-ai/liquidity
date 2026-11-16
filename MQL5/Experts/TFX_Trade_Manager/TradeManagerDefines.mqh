//+------------------------------------------------------------------+
//|                                           TradeManagerDefines.mqh |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, ToolsFX"
#property link      "https://www.toolsfx.com"
#property strict

//+------------------------------------------------------------------+
//| ENUMERATIONS                                                     |
//+------------------------------------------------------------------+
enum ENUM_RISK_MODE
{
   RISK_MODE_PERCENT,    // Risk as Percentage of Account Balance/Equity (%)
   RISK_MODE_MONEY,      // Risk as Fixed Cash Amount ($)
   RISK_MODE_FIXED_LOT   // Fixed Lot Size (Calculates resulting Risk $ and %)
};

enum ENUM_ACCOUNT_BASE
{
   ACCOUNT_BASE_BALANCE, // Account Balance
   ACCOUNT_BASE_EQUITY,  // Account Equity
   ACCOUNT_BASE_FREE_MARGIN // Free Margin
};

enum ENUM_PANEL_MODE
{
   PANEL_MODE_FULL,      // Full Mode (All controls & statistics)
   PANEL_MODE_COMPACT,   // Compact Mode (Minimal space)
   PANEL_MODE_MINIMIZED  // Minimized Toolbar (Icon only)
};

enum ENUM_TRADE_DIR
{
   TRADE_DIR_BUY,        // BUY (Long)
   TRADE_DIR_SELL        // SELL (Short)
};

enum ENUM_ORDER_EXEC_TYPE
{
   ORDER_EXEC_MARKET,    // Market / Instant Execution
   ORDER_EXEC_LIMIT,     // Limit Order (Buy Limit / Sell Limit)
   ORDER_EXEC_STOP       // Stop Order (Buy Stop / Sell Stop)
};

enum ENUM_THEME
{
   THEME_DARK,           // Dark Mode (Dark slate / neon accents)
   THEME_LIGHT           // Light Mode (Clean trading terminal)
};

//+------------------------------------------------------------------+
//| STRUCTURES                                                       |
//+------------------------------------------------------------------+
struct STradePlan
{
   ENUM_TRADE_DIR        direction;              // Buy / Sell
   ENUM_ORDER_EXEC_TYPE  order_type;             // Market / Limit / Stop
   double                entry_price;            // Entry price level
   double                sl_price;               // Stop loss price level
   double                tp_prices[3];           // Take profit levels (up to 3)
   double                tp_shares[3];           // Target volume distribution in % (e.g. 50, 30, 20)
   int                   num_targets;            // Active targets count (1, 2, or 3)
   
   double                total_lots;             // Total calculated position size
   double                target_lots[3];         // Volume for each individual target
   
   double                risk_money;             // Total money risked ($)
   double                risk_percent;           // Risk as % of account
   double                reward_money[3];        // Potential reward for each target ($)
   double                total_reward_money;     // Total potential profit ($)
   double                risk_reward_ratios[3];  // R:R for each target
   double                avg_rr_ratio;           // Average blended R:R
   
   double                sl_distance_points;     // SL distance in points
   double                sl_distance_pips;       // SL distance in pips
   double                tp_distance_points[3];  // TP distances in points
   double                tp_distance_pips[3];    // TP distances in pips
   
   bool                  follow_price;           // Whether entry line follows live price
   bool                  lock_rr;                // Whether TP moves with SL to maintain R:R
};

struct SExposureInfo
{
   string                symbol;                 // Symbol name
   double                buy_volume;             // Total buy volume (lots)
   double                sell_volume;            // Total sell volume (lots)
   double                net_volume;             // Net volume (buy - sell)
   double                floating_profit;        // Floating P&L in account currency
   double                margin_used;            // Margin used by positions of this symbol
};

//+------------------------------------------------------------------+
//| CONSTANTS & COLOR SCHEMES                                        |
//+------------------------------------------------------------------+
#define PREFIX_GUI              "TFX_GUI_"
#define PREFIX_LINE             "TFX_LINE_"
#define PREFIX_LBL              "TFX_LBL_"

// Dark Theme Colors
#define CLR_DARK_BG             C'20,24,35'
#define CLR_DARK_PANEL_BG       C'28,34,48'
#define CLR_DARK_BORDER         C'45,55,75'
#define CLR_DARK_TEXT_PRIMARY   C'240,244,248'
#define CLR_DARK_TEXT_SECONDARY C'150,165,185'
#define CLR_DARK_BUY            C'8,153,129'
#define CLR_DARK_SELL           C'242,54,69'
#define CLR_DARK_ACCENT         C'41,98,255'
#define CLR_DARK_HIGHLIGHT      C'255,179,0'

// Light Theme Colors
#define CLR_LIGHT_BG            C'240,242,245'
#define CLR_LIGHT_PANEL_BG      C'255,255,255'
#define CLR_LIGHT_BORDER        C'210,215,225'
#define CLR_LIGHT_TEXT_PRIMARY  C'25,30,40'
#define CLR_LIGHT_TEXT_SECONDARY C'100,110,125'
#define CLR_LIGHT_BUY           C'14,140,110'
#define CLR_LIGHT_SELL          C'215,40,55'
#define CLR_LIGHT_ACCENT        C'25,118,210'
#define CLR_LIGHT_HIGHLIGHT     C'245,124,0'

// Line Colors
#define CLR_LINE_ENTRY          C'41,98,255'    // Royal Blue / Cyan
#define CLR_LINE_SL             C'242,54,69'    // Red / Crimson
#define CLR_LINE_TP1            C'0,200,83'     // Vivid Green
#define CLR_LINE_TP2            C'0,230,118'    // Mint Green
#define CLR_LINE_TP3            C'105,240,174'  // Light Sea Green

