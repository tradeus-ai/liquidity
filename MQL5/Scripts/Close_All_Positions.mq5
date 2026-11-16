//+------------------------------------------------------------------+
//|                                         Close_All_Positions.mq5  |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, ToolsFX"
#property link        "https://www.toolsfx.com"
#property version     "1.00"
#property script_show_inputs
#property description "Instantly closes all open positions with a single click."

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input group "=== Close Filter ==="
input bool InpCurrentSymbolOnly = true; // Close only for current chart symbol (false = All Symbols)
input ulong InpMagicFilter      = 0;    // Magic Number Filter (0 = Any magic number)

void OnStart()
{
   CTrade trade;
   CPositionInfo pos;
   int total = PositionsTotal();
   int closed = 0;
   double closed_pnl = 0.0;

   for(int i = total - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket <= 0) continue;

      if(!pos.SelectByTicket(ticket)) continue;

      if(InpCurrentSymbolOnly && pos.Symbol() != _Symbol)
         continue;

      if(InpMagicFilter > 0 && pos.Magic() != InpMagicFilter)
         continue;

      double profit = pos.Profit();
      if(trade.PositionClose(ticket))
      {
         closed++;
         closed_pnl += profit;
         PrintFormat("Closed Position #%I64u on %s (P&L: $%.2f)", ticket, pos.Symbol(), profit);
      }
      else
      {
         PrintFormat("Failed to close Position #%I64u: %s", ticket, trade.ResultRetcodeDescription());
      }
   }

   string msg = StringFormat("CloseAllPositions: Closed %d of %d positions. Total Realized P&L: $%.2f",
                             closed, total, closed_pnl);
   Alert(msg);
}

