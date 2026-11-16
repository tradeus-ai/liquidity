//+------------------------------------------------------------------+
//|                                           Move_To_Breakeven.mq5  |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, ToolsFX"
#property link        "https://www.toolsfx.com"
#property version     "1.00"
#property script_show_inputs
#property description "Moves Stop Loss of open positions to Entry price (+ optional offset)."

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input group "=== Break-Even Settings ==="
input bool   InpCurrentSymbolOnly = true; // Apply only to current chart symbol
input double InpOffsetPoints      = 10.0; // Profit buffer in points added to BE (e.g. to cover commission)
input bool   InpOnlyIfInProfit    = true; // Only move if position is currently in profit

void OnStart()
{
   CTrade trade;
   CPositionInfo pos;
   int modified = 0;
   int scanned = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket <= 0) continue;

      if(!pos.SelectByTicket(ticket)) continue;

      if(InpCurrentSymbolOnly && pos.Symbol() != _Symbol)
         continue;

      scanned++;

      if(InpOnlyIfInProfit && pos.Profit() <= 0.0)
         continue;

      string sym = pos.Symbol();
      double open_price = pos.PriceOpen();
      double current_sl = pos.StopLoss();
      double current_tp = pos.TakeProfit();
      double pt = SymbolInfoDouble(sym, SYMBOL_POINT);
      int dg    = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);

      double new_sl = 0.0;
      if(pos.PositionType() == POSITION_TYPE_BUY)
      {
         new_sl = NormalizeDouble(open_price + InpOffsetPoints * pt, dg);
         if(current_sl < new_sl || current_sl == 0.0)
         {
            if(trade.PositionModify(ticket, new_sl, current_tp))
            {
               modified++;
               PrintFormat("Position #%I64u (%s BUY) SL moved to Break-Even at %.5f", ticket, sym, new_sl);
            }
         }
      }
      else // SELL
      {
         new_sl = NormalizeDouble(open_price - InpOffsetPoints * pt, dg);
         if(current_sl > new_sl || current_sl == 0.0)
         {
            if(trade.PositionModify(ticket, new_sl, current_tp))
            {
               modified++;
               PrintFormat("Position #%I64u (%s SELL) SL moved to Break-Even at %.5f", ticket, sym, new_sl);
            }
         }
      }
   }

   string msg = StringFormat("MoveToBreakeven: Updated %d of %d scanned positions to Break-Even (+%.1f pts).",
                             modified, scanned, InpOffsetPoints);
   Alert(msg);
}

