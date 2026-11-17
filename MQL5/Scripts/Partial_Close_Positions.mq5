//+------------------------------------------------------------------+
//|                                      Partial_Close_Positions.mq5  |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, ToolsFX"
#property link        "https://www.toolsfx.com"
#property version     "1.00"
#property script_show_inputs
#property description "Partially closes a percentage (e.g. 50%) of open positions."

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

input group "=== Partial Close Settings ==="
input double InpClosePercentage   = 50.0; // Percentage of volume to close (e.g. 50%)
input bool   InpCurrentSymbolOnly = true; // Apply only to current chart symbol
input bool   InpOnlyIfInProfit    = false;// Only partially close winning positions

void OnStart()
{
   if(InpClosePercentage <= 0.0 || InpClosePercentage >= 100.0)
   {
      Alert("Invalid close percentage: ", InpClosePercentage);
      return;
   }

   CTrade trade;
   CPositionInfo pos;
   int closed = 0;
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
      double current_vol = pos.Volume();
      double min_vol = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
      double step    = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);

      int lot_digits = 0;
      double s = step;
      while(s < 1.0 && lot_digits < 8) { s *= 10.0; lot_digits++; }

      double target_vol = current_vol * (InpClosePercentage / 100.0);
      double steps = MathFloor(target_vol / step + 0.0000001);
      double close_vol = NormalizeDouble(steps * step, lot_digits);

      // Verify broker volume restrictions
      if(close_vol >= min_vol && (current_vol - close_vol) >= min_vol)
      {
         if(trade.PositionClosePartial(ticket, close_vol))
         {
            closed++;
            PrintFormat("Partially closed %.2f lots of %.2f lots on Position #%I64u (%s)",
                        close_vol, current_vol, ticket, sym);
         }
         else
         {
            PrintFormat("Failed to partially close #%I64u: %s", ticket, trade.ResultRetcodeDescription());
         }
      }
      else
      {
         PrintFormat("Cannot partially close #%I64u: volume %.2f cannot be split (Min: %.2f, Step: %.2f)",
                     ticket, current_vol, min_vol, step);
      }
   }

   string msg = StringFormat("PartialClosePositions: Partially closed %.1f%% on %d of %d scanned positions.",
                             InpClosePercentage, closed, scanned);
   Alert(msg);
}

