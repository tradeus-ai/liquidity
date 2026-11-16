//+------------------------------------------------------------------+
//|                                              VisualTradeTool.mqh |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, ToolsFX"
#property link      "https://www.toolsfx.com"
#property strict

#include "TradeManagerDefines.mqh"
#include "RiskCalculator.mqh"

//+------------------------------------------------------------------+
//| CLASS: CVisualTradeTool                                          |
//| Manages interactive on-chart Entry, SL, and TP lines & labels    |
//+------------------------------------------------------------------+
class CVisualTradeTool
{
private:
   long                 m_chart_id;
   string               m_symbol;
   int                  m_digits;
   bool                 m_visible;

   string               m_entry_name;
   string               m_sl_name;
   string               m_tp_names[3];

   string               m_entry_lbl_name;
   string               m_sl_lbl_name;
   string               m_tp_lbl_names[3];

   color                m_col_entry;
   color                m_col_sl;
   color                m_col_tp[3];

   // Helper to format money or mask if privacy mode active
   string FormatMoney(double money, bool hide_money, string prefix = "$")
   {
      if(hide_money)
         return prefix + "***";
      return prefix + DoubleToString(money, 2);
   }

public:
   CVisualTradeTool(void)
   {
      m_chart_id = 0;
      m_symbol = "";
      m_digits = 5;
      m_visible = false;

      m_entry_name     = PREFIX_LINE + "ENTRY";
      m_sl_name        = PREFIX_LINE + "SL";
      m_tp_names[0]    = PREFIX_LINE + "TP1";
      m_tp_names[1]    = PREFIX_LINE + "TP2";
      m_tp_names[2]    = PREFIX_LINE + "TP3";

      m_entry_lbl_name  = PREFIX_LBL + "ENTRY";
      m_sl_lbl_name     = PREFIX_LBL + "SL";
      m_tp_lbl_names[0] = PREFIX_LBL + "TP1";
      m_tp_lbl_names[1] = PREFIX_LBL + "TP2";
      m_tp_lbl_names[2] = PREFIX_LBL + "TP3";

      m_col_entry = CLR_LINE_ENTRY;
      m_col_sl    = CLR_LINE_SL;
      m_col_tp[0] = CLR_LINE_TP1;
      m_col_tp[1] = CLR_LINE_TP2;
      m_col_tp[2] = CLR_LINE_TP3;
   }

   ~CVisualTradeTool(void)
   {
      RemoveAll();
   }

   //+------------------------------------------------------------------+
   //| Initialize visual tool on chart                                  |
   //+------------------------------------------------------------------+
   void Init(long chart_id, string symbol)
   {
      m_chart_id = chart_id;
      m_symbol = symbol;
      m_digits = (int)SymbolInfoInteger(m_symbol, SYMBOL_DIGITS);
   }

   //+------------------------------------------------------------------+
   //| Create or update horizontal interactive line                     |
   //+------------------------------------------------------------------+
   bool SetHLine(string name, double price, color col, ENUM_LINE_STYLE style, int width, string text)
   {
      if(ObjectFind(m_chart_id, name) < 0)
      {
         if(!ObjectCreate(m_chart_id, name, OBJ_HLINE, 0, 0, price))
            return false;
      }

      ObjectSetDouble(m_chart_id, name, OBJPROP_PRICE, price);
      ObjectSetInteger(m_chart_id, name, OBJPROP_COLOR, col);
      ObjectSetInteger(m_chart_id, name, OBJPROP_STYLE, style);
      ObjectSetInteger(m_chart_id, name, OBJPROP_WIDTH, width);
      ObjectSetInteger(m_chart_id, name, OBJPROP_SELECTABLE, true);
      ObjectSetInteger(m_chart_id, name, OBJPROP_SELECTED, false);
      ObjectSetInteger(m_chart_id, name, OBJPROP_BACK, false);
      ObjectSetString(m_chart_id, name, OBJPROP_TOOLTIP, text);

      return true;
   }

   //+------------------------------------------------------------------+
   //| Create or update price text label next to line                   |
   //+------------------------------------------------------------------+
   bool SetLineLabel(string name, double price, string text, color col, color bg_col)
   {
      datetime last_bar_time = (datetime)SeriesInfoInteger(m_symbol, Period(), SERIES_LASTBAR_DATE);
      if(last_bar_time <= 0)
         last_bar_time = TimeCurrent();

      if(ObjectFind(m_chart_id, name) < 0)
      {
         if(!ObjectCreate(m_chart_id, name, OBJ_TEXT, 0, last_bar_time, price))
            return false;
      }

      ObjectSetInteger(m_chart_id, name, OBJPROP_TIME, last_bar_time);
      ObjectSetDouble(m_chart_id, name, OBJPROP_PRICE, price);
      ObjectSetString(m_chart_id, name, OBJPROP_TEXT, "  " + text);
      ObjectSetInteger(m_chart_id, name, OBJPROP_COLOR, col);
      ObjectSetInteger(m_chart_id, name, OBJPROP_FONTSIZE, 9);
      ObjectSetString(m_chart_id, name, OBJPROP_FONT, "Segoe UI Bold");
      ObjectSetInteger(m_chart_id, name, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(m_chart_id, name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(m_chart_id, name, OBJPROP_BACK, false);

      return true;
   }

   //+------------------------------------------------------------------+
   //| Draw or refresh all active visual lines based on Trade Plan      |
   //+------------------------------------------------------------------+
   void Render(const STradePlan &plan, bool hide_money = false)
   {
      m_visible = true;

      // 1. Entry Line
      string entry_desc = (plan.direction == TRADE_DIR_BUY ? "BUY" : "SELL") + " ENTRY: " + DoubleToString(plan.entry_price, m_digits);
      SetHLine(m_entry_name, plan.entry_price, m_col_entry, STYLE_SOLID, 2, entry_desc);

      string order_str = "MARKET";
      if(plan.order_type == ORDER_EXEC_LIMIT)
         order_str = (plan.direction == TRADE_DIR_BUY) ? "BUY LIMIT" : "SELL LIMIT";
      else if(plan.order_type == ORDER_EXEC_STOP)
         order_str = (plan.direction == TRADE_DIR_BUY) ? "BUY STOP" : "SELL STOP";

      string entry_lbl_text = StringFormat("ENTRY [%s] %s | Vol: %s Lots",
                                           order_str,
                                           DoubleToString(plan.entry_price, m_digits),
                                           DoubleToString(plan.total_lots, 2));
      SetLineLabel(m_entry_lbl_name, plan.entry_price, entry_lbl_text, m_col_entry, clrBlack);

      // 2. Stop Loss Line
      string sl_desc = "SL: " + DoubleToString(plan.sl_price, m_digits);
      SetHLine(m_sl_name, plan.sl_price, m_col_sl, STYLE_SOLID, 2, sl_desc);

      string sl_lbl_text = StringFormat("SL: %s [-%s pips | -%s (%.2f%%)]",
                                        DoubleToString(plan.sl_price, m_digits),
                                        DoubleToString(plan.sl_distance_pips, 1),
                                        FormatMoney(plan.risk_money, hide_money),
                                        plan.risk_percent);
      SetLineLabel(m_sl_lbl_name, plan.sl_price, sl_lbl_text, m_col_sl, clrBlack);

      // 3. Take Profit Lines (1, 2, or 3)
      for(int i = 0; i < 3; i++)
      {
         if(i < plan.num_targets && plan.tp_prices[i] > 0.0)
         {
            string tp_desc = StringFormat("TP%d: %s", i + 1, DoubleToString(plan.tp_prices[i], m_digits));
            SetHLine(m_tp_names[i], plan.tp_prices[i], m_col_tp[i], STYLE_SOLID, 2, tp_desc);

            string tp_lbl_text = StringFormat("TP%d: %s [+%s pips | +%s | 1:%.2f RR] Vol: %s",
                                              i + 1,
                                              DoubleToString(plan.tp_prices[i], m_digits),
                                              DoubleToString(plan.tp_distance_pips[i], 1),
                                              FormatMoney(plan.reward_money[i], hide_money),
                                              plan.risk_reward_ratios[i],
                                              DoubleToString(plan.target_lots[i], 2));
            SetLineLabel(m_tp_lbl_names[i], plan.tp_prices[i], tp_lbl_text, m_col_tp[i], clrBlack);
         }
         else
         {
            // Delete inactive target lines
            ObjectDelete(m_chart_id, m_tp_names[i]);
            ObjectDelete(m_chart_id, m_tp_lbl_names[i]);
         }
      }

      ChartRedraw(m_chart_id);
   }

   //+------------------------------------------------------------------+
   //| Read current price levels from chart lines                       |
   //+------------------------------------------------------------------+
   bool ReadPrices(STradePlan &plan)
   {
      double p_entry = 0.0, p_sl = 0.0, p_tp[3] = {0.0, 0.0, 0.0};

      if(ObjectGetDouble(m_chart_id, m_entry_name, OBJPROP_PRICE, 0, p_entry) && p_entry > 0.0)
         plan.entry_price = NormalizeDouble(p_entry, m_digits);

      if(ObjectGetDouble(m_chart_id, m_sl_name, OBJPROP_PRICE, 0, p_sl) && p_sl > 0.0)
         plan.sl_price = NormalizeDouble(p_sl, m_digits);

      for(int i = 0; i < plan.num_targets; i++)
      {
         if(ObjectGetDouble(m_chart_id, m_tp_names[i], OBJPROP_PRICE, 0, p_tp[i]) && p_tp[i] > 0.0)
            plan.tp_prices[i] = NormalizeDouble(p_tp[i], m_digits);
      }

      return true;
   }

   //+------------------------------------------------------------------+
   //| Handle chart drag events                                         |
   //+------------------------------------------------------------------+
   bool HandleChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam, STradePlan &plan)
   {
      if(id != CHARTEVENT_OBJECT_DRAG)
         return false;

      // User dragged Entry line
      if(sparam == m_entry_name)
      {
         double new_price = 0.0;
         if(ObjectGetDouble(m_chart_id, m_entry_name, OBJPROP_PRICE, 0, new_price))
         {
            plan.entry_price = NormalizeDouble(new_price, m_digits);
            return true;
         }
      }

      // User dragged SL line
      if(sparam == m_sl_name)
      {
         double new_sl = 0.0;
         if(ObjectGetDouble(m_chart_id, m_sl_name, OBJPROP_PRICE, 0, new_sl))
         {
            double old_sl = plan.sl_price;
            plan.sl_price = NormalizeDouble(new_sl, m_digits);

            // If Lock R:R is enabled, shift TPs to maintain existing R:R ratio!
            if(plan.lock_rr && old_sl > 0.0 && plan.entry_price > 0.0)
            {
               double old_risk_dist = MathAbs(plan.entry_price - old_sl);
               double new_risk_dist = MathAbs(plan.entry_price - plan.sl_price);

               if(old_risk_dist > 0.0000001)
               {
                  for(int i = 0; i < plan.num_targets; i++)
                  {
                     if(plan.tp_prices[i] > 0.0)
                     {
                        double rr = MathAbs(plan.tp_prices[i] - plan.entry_price) / old_risk_dist;
                        double new_tp_dist = new_risk_dist * rr;
                        if(plan.direction == TRADE_DIR_BUY)
                           plan.tp_prices[i] = NormalizeDouble(plan.entry_price + new_tp_dist, m_digits);
                        else
                           plan.tp_prices[i] = NormalizeDouble(plan.entry_price - new_tp_dist, m_digits);
                     }
                  }
               }
            }
            return true;
         }
      }

      // User dragged a TP line
      for(int i = 0; i < 3; i++)
      {
         if(sparam == m_tp_names[i])
         {
            double new_tp = 0.0;
            if(ObjectGetDouble(m_chart_id, m_tp_names[i], OBJPROP_PRICE, 0, new_tp))
            {
               plan.tp_prices[i] = NormalizeDouble(new_tp, m_digits);
               return true;
            }
         }
      }

      return false;
   }

   //+------------------------------------------------------------------+
   //| Follow live market price for instant entry orders                |
   //+------------------------------------------------------------------+
   void FollowPriceTick(STradePlan &plan)
   {
      if(!plan.follow_price || plan.order_type != ORDER_EXEC_MARKET)
         return;

      double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      double live_price = (plan.direction == TRADE_DIR_BUY) ? ask : bid;

      if(live_price <= 0.0 || MathAbs(live_price - plan.entry_price) < (m_digits > 3 ? 0.00001 : 0.01))
         return;

      double price_shift = live_price - plan.entry_price;
      plan.entry_price = NormalizeDouble(live_price, m_digits);

      // Shift SL and TPs simultaneously to keep exact pip risk/reward geometry
      if(plan.sl_price > 0.0)
         plan.sl_price = NormalizeDouble(plan.sl_price + price_shift, m_digits);

      for(int i = 0; i < plan.num_targets; i++)
      {
         if(plan.tp_prices[i] > 0.0)
            plan.tp_prices[i] = NormalizeDouble(plan.tp_prices[i] + price_shift, m_digits);
      }

      Render(plan);
   }

   //+------------------------------------------------------------------+
   //| Remove all lines and labels from chart                           |
   //+------------------------------------------------------------------+
   void RemoveAll(void)
   {
      ObjectDelete(m_chart_id, m_entry_name);
      ObjectDelete(m_chart_id, m_sl_name);
      ObjectDelete(m_chart_id, m_entry_lbl_name);
      ObjectDelete(m_chart_id, m_sl_lbl_name);

      for(int i = 0; i < 3; i++)
      {
         ObjectDelete(m_chart_id, m_tp_names[i]);
         ObjectDelete(m_chart_id, m_tp_lbl_names[i]);
      }

      m_visible = false;
      ChartRedraw(m_chart_id);
   }

   //+------------------------------------------------------------------+
   //| Toggle visibility                                                |
   //+------------------------------------------------------------------+
   void ToggleVisibility(const STradePlan &plan)
   {
      if(m_visible)
         RemoveAll();
      else
         Render(plan);
   }

   bool IsVisible(void) const { return m_visible; }
};

