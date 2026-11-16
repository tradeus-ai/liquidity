//+------------------------------------------------------------------+
//|                                       TFX_Trade_Manager_EA.mq5   |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, ToolsFX"
#property link        "https://www.toolsfx.com"
#property version     "3.24"
#property description "TFX Trade Manager EA & Visual Risk Calculator"
#property description "Fast, Single-Click Trade Execution with Precise Multi-Target Lot Sizing,"
#property description "Visual Drag-and-Drop Risk/Reward Lines, Account Exposure, and Trade Management."

#include "TradeManagerDefines.mqh"
#include "RiskCalculator.mqh"
#include "VisualTradeTool.mqh"
#include "TradeManagerGUI.mqh"
#include "OrderExecution.mqh"
#include "HotkeyHandler.mqh"

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                 |
//+------------------------------------------------------------------+
input group "=== Risk Management ==="
input ENUM_RISK_MODE    InpDefaultRiskMode      = RISK_MODE_PERCENT;    // Default Risk Mode
input double            InpDefaultRiskValue     = 1.0;                  // Default Risk Value (% / $ / Lots)
input ENUM_ACCOUNT_BASE InpAccountBase          = ACCOUNT_BASE_BALANCE; // Account Base for % Calculation
input bool              InpHideMonetaryValues   = false;                // Hide Monetary Values (Privacy Mode)

input group "=== Multi-Target & Volume Scaling ==="
input int               InpDefaultTargets       = 2;                    // Number of Targets (1, 2, or 3)
input double            InpTarget1Share         = 50.0;                 // Target 1 Volume Share (%)
input double            InpTarget2Share         = 30.0;                 // Target 2 Volume Share (%)
input double            InpTarget3Share         = 20.0;                 // Target 3 Volume Share (%)
input double            InpDefaultRR            = 2.0;                  // Default Risk:Reward Ratio
input bool              InpLockRR               = false;                // Lock Risk:Reward on Drag

input group "=== Order Execution ==="
input ulong             InpMagicNumber          = 8882026;              // EA Magic Number
input ulong             InpSlippage             = 10;                   // Max Slippage in Points
input string            InpOrderComment         = "TFX Trade Manager";  // Order Comment

input group "=== Automation: Auto Break-Even & Trailing ==="
input bool              InpEnableAutoBE         = true;                 // Enable Auto Break-Even
input double            InpAutoBE_Points        = 250.0;                // Auto BE Trigger in Points
input double            InpAutoBE_Offset        = 20.0;                 // Auto BE Profit Offset in Points
input bool              InpEnableTrailing       = false;                // Enable Trailing Stop
input double            InpTrailingStart_Points = 350.0;                // Trailing Start in Points
input double            InpTrailingStop_Points  = 200.0;                // Trailing Distance in Points
input double            InpTrailingStep_Points  = 50.0;                 // Trailing Step in Points

input group "=== User Interface & Theme ==="
input ENUM_THEME        InpTheme                = THEME_DARK;           // UI Color Theme
input bool              InpStartMinimized       = false;                // Start Minimized
input bool              InpFollowPriceDefault   = false;                // Follow Live Market Price

//+------------------------------------------------------------------+
//| GLOBAL OBJECTS & STATE                                           |
//+------------------------------------------------------------------+
CRiskCalculator         g_calc;
CVisualTradeTool        g_visual;
CTradeManagerGUI        g_gui;
COrderExecution         g_exec;

STradePlan              g_plan;
ENUM_RISK_MODE          g_risk_mode;
double                  g_risk_input_val;
int                     g_digits;
double                  g_point;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   g_digits = _Digits;
   g_point  = _Point;

   // 1. Initialize Engines
   g_calc.InitSymbol(_Symbol);
   g_visual.Init(ChartID(), _Symbol);
   g_gui.Init(ChartID(), _Symbol, InpTheme, InpHideMonetaryValues);
   g_exec.Init(_Symbol, InpMagicNumber, InpSlippage);

   if(InpStartMinimized)
      g_gui.SetPanelMode(PANEL_MODE_MINIMIZED);

   // 2. Initialize Trade Plan Defaults
   g_risk_mode      = InpDefaultRiskMode;
   g_risk_input_val = InpDefaultRiskValue;

   g_plan.direction    = TRADE_DIR_BUY;
   g_plan.order_type   = ORDER_EXEC_MARKET;
   g_plan.num_targets  = MathMin(3, MathMax(1, InpDefaultTargets));
   g_plan.follow_price = InpFollowPriceDefault;
   g_plan.lock_rr      = InpLockRR;

   g_plan.tp_shares[0] = InpTarget1Share;
   g_plan.tp_shares[1] = InpTarget2Share;
   g_plan.tp_shares[2] = InpTarget3Share;

   // Establish initial price bracket
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask <= 0.0) ask = Close[0];

   g_plan.entry_price = NormalizeDouble(ask, g_digits);
   
   // Default SL distance = 300 points (30 pips)
   double default_sl_dist = 300.0 * g_point;
   g_plan.sl_price = NormalizeDouble(g_plan.entry_price - default_sl_dist, g_digits);

   // Setup default TPs based on R:R
   for(int i = 0; i < 3; i++)
   {
      double mult = (i == 0) ? InpDefaultRR : (InpDefaultRR + (i * 1.0));
      g_plan.tp_prices[i] = NormalizeDouble(g_plan.entry_price + default_sl_dist * mult, g_digits);
   }

   // 3. Compute initial sizing
   g_calc.CalculatePlan(g_plan, g_risk_mode, g_risk_input_val, InpAccountBase);

   // 4. Render Visual Lines and GUI Panel
   g_visual.Render(g_plan, InpHideMonetaryValues);
   g_gui.RenderMainPanel(g_plan, g_risk_mode, g_risk_input_val);

   Print("TFX Trade Manager EA Initialized successfully on ", _Symbol);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   g_visual.RemoveAll();
   g_gui.DestroyAll();
   Comment("");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // 1. Follow Live Market Price (if enabled)
   if(g_plan.follow_price && g_plan.order_type == ORDER_EXEC_MARKET)
   {
      g_visual.FollowPriceTick(g_plan);
      g_calc.CalculatePlan(g_plan, g_risk_mode, g_risk_input_val, InpAccountBase);
      g_visual.Render(g_plan, InpHideMonetaryValues);
      g_gui.RenderMainPanel(g_plan, g_risk_mode, g_risk_input_val);
   }

   // 2. Automated Trade Management (BE and Trailing)
   if(InpEnableAutoBE)
   {
      g_exec.CheckAutoBreakEven(InpAutoBE_Points, InpAutoBE_Offset, true);
   }

   if(InpEnableTrailing)
   {
      g_exec.CheckTrailingStop(InpTrailingStart_Points, InpTrailingStop_Points, InpTrailingStep_Points, true);
   }

   // 3. Keep open trades & exposure stats updated if windows open
   g_gui.RenderTradesWindow(g_exec);
   g_gui.RenderExposureWindow();
}

//+------------------------------------------------------------------+
//| ChartEvent function                                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   bool plan_changed = false;

   // 1. Handle Hotkeys
   if(id == CHARTEVENT_KEYDOWN)
   {
      if(CHotkeyHandler::ProcessKeyEvent(id, lparam, dparam, sparam, g_plan, g_visual, g_gui, g_exec))
      {
         plan_changed = true;
      }
   }

   // 2. Handle On-Chart Line Dragging
   if(id == CHARTEVENT_OBJECT_DRAG)
   {
      if(g_visual.HandleChartEvent(id, lparam, dparam, sparam, g_plan))
      {
         plan_changed = true;
      }
   }

   // 3. Handle GUI Button Clicks and Edit Inputs
   if(id == CHARTEVENT_OBJECT_CLICK || id == CHARTEVENT_OBJECT_ENDEDIT)
   {
      if(g_gui.HandleChartEvent(id, lparam, dparam, sparam, g_plan, g_risk_mode, g_risk_input_val, g_exec, g_visual))
      {
         plan_changed = true;
      }
   }

   // 4. If any user action modified parameters, recalculate and re-render
   if(plan_changed)
   {
      g_calc.CalculatePlan(g_plan, g_risk_mode, g_risk_input_val, InpAccountBase);
      g_visual.Render(g_plan, InpHideMonetaryValues);
      g_gui.RenderMainPanel(g_plan, g_risk_mode, g_risk_input_val);
      g_gui.RenderTradesWindow(g_exec);
      g_gui.RenderExposureWindow();
   }
}
//+------------------------------------------------------------------+

