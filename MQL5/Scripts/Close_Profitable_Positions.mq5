//+------------------------------------------------------------------+
//|                                  Close_Profitable_Positions.mq5  |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, ToolsFX"
#property link        "https://www.toolsfx.com"
#property version     "1.00"
#property script_show_inputs
#property description "Instantly closes only winning/profitable open positions."

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input group "=== Close Filter ==="
input bool InpCurrentSymbolOnly = true; // Close only for current chart symbol (false = All Symbols)
input double InpMinProfitDollar = 0.01; // Minimum profit in account currency to close

void OnStart()
{
   CTrade trade;
   CPositionInfo pos;
   int total = PositionsTotal();
   int closed = 0;
   double locked_profit = 0.0;

   for(int i = total - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket <= 0) continue;

      if(!pos.SelectByTicket(ticket)) continue;

      if(InpCurrentSymbolOnly && pos.Symbol() != _Symbol)
         continue;

      double profit = pos.Profit();
      if(profit >= InpMinProfitDollar)
      {
         if(trade.PositionClose(ticket))
         {
            closed++;
            locked_profit += profit;
            PrintFormat("Closed Winner #%I64u on %s with Profit: +$%.2f", ticket, pos.Symbol(), profit);
         }
      }
   }

   string msg = StringFormat("CloseProfitablePositions: Closed %d winning positions. Total Profit Secured: +$%.2f",
                             closed, locked_profit);
   Alert(msg);
}

