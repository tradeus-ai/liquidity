//+------------------------------------------------------------------+
//|                                     Auto_Risk_Order_Placer.mq5   |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, ToolsFX"
#property link        "https://www.toolsfx.com"
#property version     "1.00"
#property script_show_inputs
#property description "Auto-calculates exact position sizing from Risk % or $ amount and places"
#property description "multi-target trades with SL and Take Profits in a single click."

#include <Trade\Trade.mqh>

enum ENUM_SCRIPT_DIR
{
   DIR_BUY,  // BUY (Long)
   DIR_SELL  // SELL (Short)
};

enum ENUM_SCRIPT_ORDER_TYPE
{
   TYPE_MARKET, // Market Order
   TYPE_LIMIT,  // Limit Order
   TYPE_STOP    // Stop Order
};

enum ENUM_SCRIPT_RISK_MODE
{
   MODE_PERCENT, // Risk as % of Account Balance
   MODE_AMOUNT   // Risk as Fixed Cash Amount ($)
};

//+------------------------------------------------------------------+
//| SCRIPT INPUTS                                                    |
//+------------------------------------------------------------------+
input group "=== Risk Configuration ==="
input ENUM_SCRIPT_RISK_MODE InpRiskMode        = MODE_PERCENT; // Risk Calculation Mode
input double                InpRiskValue       = 1.0;          // Risk Value (1.0 = 1.0% or $100 if Amount)
input double                InpStopLossPips    = 25.0;         // Stop Loss Distance in Pips

input group "=== Trade Setup ==="
input ENUM_SCRIPT_DIR       InpDirection       = DIR_BUY;      // Trade Direction
input ENUM_SCRIPT_ORDER_TYPE InpOrderType      = TYPE_MARKET;  // Order Type
input double                InpPendingOffsetPips = 0.0;        // Pending Price Offset in Pips (0 = at current price)
input int                   InpTargetsCount    = 2;            // Number of Take Profit Targets (1, 2, or 3)
input double                InpTarget1_RR      = 1.5;          // Target 1 Risk:Reward Ratio
input double                InpTarget2_RR      = 2.5;          // Target 2 Risk:Reward Ratio
input double                InpTarget3_RR      = 4.0;          // Target 3 Risk:Reward Ratio

input group "=== Target Volume Distribution ==="
input double                InpTarget1_Share   = 50.0;         // Target 1 Share (%)
input double                InpTarget2_Share   = 30.0;         // Target 2 Share (%)
input double                InpTarget3_Share   = 20.0;         // Target 3 Share (%)

input group "=== Execution Settings ==="
input ulong                 InpMagicNumber     = 8881001;      // Magic Number
input ulong                 InpSlippage        = 10;           // Max Slippage in Points
input string                InpComment         = "AutoRiskPlacer"; // Order Comment

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
   string symbol = _Symbol;
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double tick_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick_size <= 0.0) tick_size = point;
   double tick_val = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tick_val <= 0.0) tick_val = 1.0;

   double vol_min = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double vol_max = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double vol_step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   int lot_digits = 0;
   double s = vol_step;
   while(s < 1.0 && lot_digits < 8) { s *= 10.0; lot_digits++; }

   // 1. Determine Entry Price
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double entry_price = (InpDirection == DIR_BUY) ? ask : bid;

   if(InpOrderType != TYPE_MARKET && InpPendingOffsetPips != 0.0)
   {
      double offset = InpPendingOffsetPips * 10.0 * point;
      entry_price = (InpDirection == DIR_BUY) ? (entry_price + offset) : (entry_price - offset);
   }
   entry_price = NormalizeDouble(entry_price, digits);

   // 2. Determine Stop Loss Price
   double sl_diff = InpStopLossPips * 10.0 * point;
   double sl_price = (InpDirection == DIR_BUY) ? (entry_price - sl_diff) : (entry_price + sl_diff);
   sl_price = NormalizeDouble(sl_price, digits);

   // 3. Calculate Loss per 1.0 Lot
   ENUM_ORDER_TYPE ot = (InpDirection == DIR_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double loss_1_lot = 0.0;

   // OrderCalcProfit returns SIGNED profit (negative for a losing exit): take the
   // absolute value BEFORE testing success, or valid results are wrongly discarded.
   bool calc_ok = OrderCalcProfit(ot, symbol, 1.0, entry_price, sl_price, loss_1_lot);
   loss_1_lot = MathAbs(loss_1_lot);
   if(!calc_ok || loss_1_lot <= 0.000001)
   {
      loss_1_lot = MathAbs((sl_diff / tick_size) * tick_val);
   }

   if(loss_1_lot <= 0.000001)
   {
      Alert("Error: Could not calculate loss per lot for symbol ", symbol);
      return;
   }

   // 4. Calculate Risk Cash & Position Size
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_cash = (InpRiskMode == MODE_PERCENT) ? (balance * (InpRiskValue / 100.0)) : InpRiskValue;

   double raw_lots = risk_cash / loss_1_lot;
   double steps = MathFloor(raw_lots / vol_step + 0.0000001);
   double total_lots = NormalizeDouble(steps * vol_step, lot_digits);

   if(total_lots < vol_min) total_lots = vol_min;
   if(total_lots > vol_max) total_lots = vol_max;

   // 5. Target Take Profit Levels & Splitting
   int num_targets = MathMin(3, MathMax(1, InpTargetsCount));
   double rr_targets[3] = { InpTarget1_RR, InpTarget2_RR, InpTarget3_RR };
   double shares[3]     = { InpTarget1_Share, InpTarget2_Share, InpTarget3_Share };
   double target_lots[3];
   double tp_prices[3];

   double share_sum = 0.0;
   for(int i = 0; i < num_targets; i++) share_sum += shares[i];
   if(share_sum <= 0.0) share_sum = 100.0;

   double allocated_lots = 0.0;
   for(int i = 0; i < num_targets; i++)
   {
      double raw_t_lot = total_lots * (shares[i] / share_sum);
      double t_steps = MathFloor(raw_t_lot / vol_step + 0.0000001);
      target_lots[i] = NormalizeDouble(t_steps * vol_step, lot_digits);
      if(target_lots[i] < vol_min && total_lots >= vol_min && i == 0)
         target_lots[i] = vol_min;
      allocated_lots += target_lots[i];

      double tp_diff = sl_diff * rr_targets[i];
      tp_prices[i] = (InpDirection == DIR_BUY) ? (entry_price + tp_diff) : (entry_price - tp_diff);
      tp_prices[i] = NormalizeDouble(tp_prices[i], digits);
   }

   // Allocate remaining remainder to Target 1
   double rem = NormalizeDouble(total_lots - allocated_lots, lot_digits);
   if(MathAbs(rem) >= vol_step)
   {
      target_lots[0] = NormalizeDouble(target_lots[0] + rem, lot_digits);
   }

   // 6. Execute Trades via CTrade
   CTrade trade;
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFillingBySymbol(symbol);

   PrintFormat("=== Auto Risk Placer Execution ===");
   PrintFormat("Symbol: %s | Direction: %s | Total Lots: %.2f | Risk: $%.2f",
               symbol, (InpDirection == DIR_BUY ? "BUY" : "SELL"), total_lots, total_lots * loss_1_lot);

   int placed = 0;
   for(int i = 0; i < num_targets; i++)
   {
      if(target_lots[i] <= 0.0) continue;

      string sub_comment = StringFormat("%s-T%d", InpComment, i + 1);

      if(InpOrderType == TYPE_MARKET)
      {
         bool ok = false;
         if(InpDirection == DIR_BUY)
            ok = trade.PositionOpen(symbol, ORDER_TYPE_BUY, target_lots[i], ask, sl_price, tp_prices[i], sub_comment);
         else
            ok = trade.PositionOpen(symbol, ORDER_TYPE_SELL, target_lots[i], bid, sl_price, tp_prices[i], sub_comment);

         if(ok)
         {
            PrintFormat("Target %d placed: Ticket #%I64u | Vol: %.2f | TP: %.5f", i + 1, trade.ResultOrder(), target_lots[i], tp_prices[i]);
            placed++;
         }
         else
         {
            PrintFormat("Target %d failed: %s", i + 1, trade.ResultRetcodeDescription());
         }
      }
      else
      {
         ENUM_ORDER_TYPE pend_type;
         if(InpDirection == DIR_BUY)
            pend_type = (entry_price < ask) ? ORDER_TYPE_BUY_LIMIT : ORDER_TYPE_BUY_STOP;
         else
            pend_type = (entry_price > bid) ? ORDER_TYPE_SELL_LIMIT : ORDER_TYPE_SELL_STOP;

         bool ok = trade.OrderOpen(symbol, pend_type, target_lots[i], 0.0, entry_price, sl_price, tp_prices[i], ORDER_TIME_GTC, 0, sub_comment);
         if(ok)
         {
            PrintFormat("Pending Target %d placed: Ticket #%I64u | Vol: %.2f", i + 1, trade.ResultOrder(), target_lots[i]);
            placed++;
         }
      }
   }

   string summary = StringFormat("AutoRiskPlacer: Placed %d of %d orders. Total Vol: %.2f lots, Risk: $%.2f (%.1f pips)",
                                 placed, num_targets, total_lots, total_lots * loss_1_lot, InpStopLossPips);
   Alert(summary);
}

