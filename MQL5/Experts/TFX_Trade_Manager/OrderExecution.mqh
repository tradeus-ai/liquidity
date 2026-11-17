//+------------------------------------------------------------------+
//|                                               OrderExecution.mqh |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, ToolsFX"
#property link      "https://www.toolsfx.com"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>
#include "TradeManagerDefines.mqh"
#include "RiskCalculator.mqh"

//+------------------------------------------------------------------+
//| CLASS: COrderExecution                                           |
//| Handles multi-target execution, auto break-even, & trailing stop |
//+------------------------------------------------------------------+
class COrderExecution
{
private:
   CTrade               m_trade;
   CPositionInfo        m_pos_info;
   COrderInfo           m_order_info;
   string               m_symbol;
   ulong                m_magic;
   ulong                m_slippage;
   int                  m_digits;
   double               m_point;

public:
   COrderExecution(void)
   {
      m_symbol   = _Symbol;
      m_magic    = 8882026;
      m_slippage = 10;
      m_digits   = _Digits;
      m_point    = _Point;
   }

   //+------------------------------------------------------------------+
   //| Initialize execution engine                                      |
   //+------------------------------------------------------------------+
   void Init(string symbol, ulong magic, ulong slippage)
   {
      m_symbol   = (symbol == "" || symbol == NULL) ? _Symbol : symbol;
      m_magic    = magic;
      m_slippage = slippage;
      m_digits   = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);
      m_point    = SymbolInfoDouble(m_symbol, SYMBOL_POINT);

      m_trade.SetExpertMagicNumber(m_magic);
      m_trade.SetDeviationInPoints(m_slippage);
      m_trade.SetTypeFillingBySymbol(m_symbol);
   }

   //+------------------------------------------------------------------+
   //| Execute multi-target trade plan                                  |
   //+------------------------------------------------------------------+
   bool ExecutePlan(const STradePlan &plan, string comment = "TFX Trade Manager")
   {
      if(plan.total_lots <= 0.0)
      {
         Alert("TFX Trade Manager: Invalid lot size: ", plan.total_lots);
         return false;
      }

      // Netting accounts merge same-symbol positions: collapse multi-target splits
      // into one combined position (mirrors EarnForex Position Sizer behavior).
      bool netting_collapse = ((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE) == ACCOUNT_MARGIN_MODE_RETAIL_NETTING && plan.num_targets > 1);
      if(netting_collapse)
         Print("TFX Trade Manager: Netting account - placing single combined position of ", DoubleToString(plan.total_lots, 2), " lots (TP1).");

      int eff_targets = netting_collapse ? 1 : plan.num_targets;
      int orders_sent = 0;
      double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);

      // Loop through each active target and place individual order/position
      for(int i = 0; i < eff_targets; i++)
      {
         double lot = netting_collapse ? plan.total_lots : plan.target_lots[i];
         if(lot <= 0.0)
         {
            PrintFormat("TFX Trade Manager: Target %d skipped - allocated volume below broker minimum.", i + 1);
            continue;
         }

         double tp = plan.tp_prices[i];
         string sub_comment = StringFormat("%s-T%d", comment, i + 1);

         // 1. Market Instant Order
         if(plan.order_type == ORDER_EXEC_MARKET)
         {
            bool success = false;
            if(plan.direction == TRADE_DIR_BUY)
            {
               success = m_trade.PositionOpen(m_symbol, ORDER_TYPE_BUY, lot, ask, plan.sl_price, tp, sub_comment);
            }
            else
            {
               success = m_trade.PositionOpen(m_symbol, ORDER_TYPE_SELL, lot, bid, plan.sl_price, tp, sub_comment);
            }

            if(success)
            {
               PrintFormat("TFX Trade Manager: Target %d Market %s Opened successfully! Ticket: %I64u, Vol: %.2f, SL: %.5f, TP: %.5f",
                           i + 1,
                           (plan.direction == TRADE_DIR_BUY ? "BUY" : "SELL"),
                           m_trade.ResultOrder(),
                           lot,
                           plan.sl_price,
                           tp);
               orders_sent++;
            }
            else
            {
               PrintFormat("TFX Trade Manager: Error opening Target %d: %s (Retcode: %d)",
                           i + 1,
                           m_trade.ResultRetcodeDescription(),
                           m_trade.ResultRetcode());
            }
         }
         // 2. Pending Orders (Limit / Stop)
         else
         {
            ENUM_ORDER_TYPE pending_type;

            if(plan.direction == TRADE_DIR_BUY)
            {
               if(plan.entry_price < ask)
                  pending_type = ORDER_TYPE_BUY_LIMIT;
               else
                  pending_type = ORDER_TYPE_BUY_STOP;
            }
            else
            {
               if(plan.entry_price > bid)
                  pending_type = ORDER_TYPE_SELL_LIMIT;
               else
                  pending_type = ORDER_TYPE_SELL_STOP;
            }

            bool success = m_trade.OrderOpen(m_symbol,
                                             pending_type,
                                             lot,
                                             0.0,
                                             plan.entry_price,
                                             plan.sl_price,
                                             tp,
                                             ORDER_TIME_GTC,
                                             0,
                                             sub_comment);

            if(success)
            {
               PrintFormat("TFX Trade Manager: Pending Target %d placed successfully! Ticket: %I64u, Price: %.5f, Vol: %.2f",
                           i + 1,
                           m_trade.ResultOrder(),
                           plan.entry_price,
                           lot);
               orders_sent++;
            }
            else
            {
               PrintFormat("TFX Trade Manager: Error placing pending Target %d: %s (Retcode: %d)",
                           i + 1,
                           m_trade.ResultRetcodeDescription(),
                           m_trade.ResultRetcode());
            }
         }
      }

      return (orders_sent > 0);
   }

   //+------------------------------------------------------------------+
   //| Auto Break-Even Check (Called on tick)                           |
   //+------------------------------------------------------------------+
   void CheckAutoBreakEven(double trigger_points, double offset_points, bool filter_symbol = true)
   {
      if(trigger_points <= 0.0)
         return;

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;

         if(!m_pos_info.SelectByTicket(ticket))
            continue;

         if(filter_symbol && m_pos_info.Symbol() != m_symbol)
            continue;

         if(m_magic > 0 && m_pos_info.Magic() != m_magic)
            continue;

         double open_price = m_pos_info.PriceOpen();
         double current_sl = m_pos_info.StopLoss();
         double current_tp = m_pos_info.TakeProfit();
         ENUM_POSITION_TYPE p_type = m_pos_info.PositionType();

         double current_price = (p_type == POSITION_TYPE_BUY) ?
                                SymbolInfoDouble(m_pos_info.Symbol(), SYMBOL_BID) :
                                SymbolInfoDouble(m_pos_info.Symbol(), SYMBOL_ASK);

         double pt = SymbolInfoDouble(m_pos_info.Symbol(), SYMBOL_POINT);
         int dg    = (int)SymbolInfoInteger(m_pos_info.Symbol(), SYMBOL_DIGITS);

         if(p_type == POSITION_TYPE_BUY)
         {
            double profit_pts = (current_price - open_price) / pt;
            if(profit_pts >= trigger_points)
            {
               double new_sl = NormalizeDouble(open_price + offset_points * pt, dg);
               if(current_sl < new_sl || current_sl == 0.0)
               {
                  if(m_trade.PositionModify(ticket, new_sl, current_tp))
                     PrintFormat("TFX Trade Manager: Position #%I64u moved to Break-Even at %.5f (Profit: %.1f pts)",
                                 ticket, new_sl, profit_pts);
               }
            }
         }
         else // SELL
         {
            double profit_pts = (open_price - current_price) / pt;
            if(profit_pts >= trigger_points)
            {
               double new_sl = NormalizeDouble(open_price - offset_points * pt, dg);
               if(current_sl > new_sl || current_sl == 0.0)
               {
                  if(m_trade.PositionModify(ticket, new_sl, current_tp))
                     PrintFormat("TFX Trade Manager: Position #%I64u moved to Break-Even at %.5f (Profit: %.1f pts)",
                                 ticket, new_sl, profit_pts);
               }
            }
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Trailing Stop Check (Called on tick)                             |
   //+------------------------------------------------------------------+
   void CheckTrailingStop(double trailing_start_pts, double trailing_stop_pts, double trailing_step_pts, bool filter_symbol = true)
   {
      if(trailing_stop_pts <= 0.0)
         return;

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;

         if(!m_pos_info.SelectByTicket(ticket))
            continue;

         if(filter_symbol && m_pos_info.Symbol() != m_symbol)
            continue;

         if(m_magic > 0 && m_pos_info.Magic() != m_magic)
            continue;

         double open_price = m_pos_info.PriceOpen();
         double current_sl = m_pos_info.StopLoss();
         double current_tp = m_pos_info.TakeProfit();
         ENUM_POSITION_TYPE p_type = m_pos_info.PositionType();

         double current_price = (p_type == POSITION_TYPE_BUY) ?
                                SymbolInfoDouble(m_pos_info.Symbol(), SYMBOL_BID) :
                                SymbolInfoDouble(m_pos_info.Symbol(), SYMBOL_ASK);

         double pt = SymbolInfoDouble(m_pos_info.Symbol(), SYMBOL_POINT);
         int dg    = (int)SymbolInfoInteger(m_pos_info.Symbol(), SYMBOL_DIGITS);

         if(p_type == POSITION_TYPE_BUY)
         {
            double profit_pts = (current_price - open_price) / pt;
            if(profit_pts >= trailing_start_pts)
            {
               double new_sl = NormalizeDouble(current_price - trailing_stop_pts * pt, dg);
               if(new_sl > current_sl + trailing_step_pts * pt || current_sl == 0.0)
               {
                  m_trade.PositionModify(ticket, new_sl, current_tp);
               }
            }
         }
         else // SELL
         {
            double profit_pts = (open_price - current_price) / pt;
            if(profit_pts >= trailing_start_pts)
            {
               double new_sl = NormalizeDouble(current_price + trailing_stop_pts * pt, dg);
               if(new_sl < current_sl - trailing_step_pts * pt || current_sl == 0.0)
               {
                  m_trade.PositionModify(ticket, new_sl, current_tp);
               }
            }
         }
      }
   }

   //+------------------------------------------------------------------+
   //| Close all positions                                              |
   //+------------------------------------------------------------------+
   int CloseAllPositions(string symbol_filter = "")
   {
      int closed = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;

         if(!m_pos_info.SelectByTicket(ticket))
            continue;

         if(symbol_filter != "" && m_pos_info.Symbol() != symbol_filter)
            continue;

         if(m_trade.PositionClose(ticket))
            closed++;
      }
      return closed;
   }

   //+------------------------------------------------------------------+
   //| Close winning positions only                                     |
   //+------------------------------------------------------------------+
   int CloseProfitablePositions(string symbol_filter = "")
   {
      int closed = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;

         if(!m_pos_info.SelectByTicket(ticket))
            continue;

         if(symbol_filter != "" && m_pos_info.Symbol() != symbol_filter)
            continue;

         if(m_pos_info.Profit() > 0.0)
         {
            if(m_trade.PositionClose(ticket))
               closed++;
         }
      }
      return closed;
   }

   //+------------------------------------------------------------------+
   //| Close losing positions only                                      |
   //+------------------------------------------------------------------+
   int CloseLosingPositions(string symbol_filter = "")
   {
      int closed = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;

         if(!m_pos_info.SelectByTicket(ticket))
            continue;

         if(symbol_filter != "" && m_pos_info.Symbol() != symbol_filter)
            continue;

         if(m_pos_info.Profit() < 0.0)
         {
            if(m_trade.PositionClose(ticket))
               closed++;
         }
      }
      return closed;
   }

   //+------------------------------------------------------------------+
   //| Partial close percentage (e.g. 50%) of open positions            |
   //+------------------------------------------------------------------+
   int PartialClosePositions(double percent, string symbol_filter = "")
   {
      if(percent <= 0.0 || percent >= 100.0)
         return 0;

      int partial_closed = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;

         if(!m_pos_info.SelectByTicket(ticket))
            continue;

         if(symbol_filter != "" && m_pos_info.Symbol() != symbol_filter)
            continue;

         string sym = m_pos_info.Symbol();
         double pos_vol = m_pos_info.Volume();
         double step = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
         double min_vol = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);

         double close_vol = pos_vol * (percent / 100.0);
         double steps = MathFloor(close_vol / step + 0.0000001);
         close_vol = steps * step;

         if(close_vol >= min_vol && (pos_vol - close_vol) >= min_vol)
         {
            if(m_trade.PositionClosePartial(ticket, close_vol))
               partial_closed++;
         }
      }
      return partial_closed;
   }

   //+------------------------------------------------------------------+
   //| Move all positions to Break-Even                                 |
   //+------------------------------------------------------------------+
   int BreakEvenAllPositions(string symbol_filter = "", double offset_points = 0.0)
   {
      int modified = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0) continue;

         if(!m_pos_info.SelectByTicket(ticket))
            continue;

         if(symbol_filter != "" && m_pos_info.Symbol() != symbol_filter)
            continue;

         string sym = m_pos_info.Symbol();
         double open_price = m_pos_info.PriceOpen();
         double current_tp = m_pos_info.TakeProfit();
         double pt = SymbolInfoDouble(sym, SYMBOL_POINT);
         int dg    = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);

         double new_sl = 0.0;
         if(m_pos_info.PositionType() == POSITION_TYPE_BUY)
            new_sl = NormalizeDouble(open_price + offset_points * pt, dg);
         else
            new_sl = NormalizeDouble(open_price - offset_points * pt, dg);

         if(m_trade.PositionModify(ticket, new_sl, current_tp))
            modified++;
      }
      return modified;
   }
};

