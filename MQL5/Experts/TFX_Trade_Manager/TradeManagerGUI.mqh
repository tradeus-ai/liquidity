//+------------------------------------------------------------------+
//|                                              TradeManagerGUI.mqh |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, ToolsFX"
#property link      "https://www.toolsfx.com"
#property strict

#include <ChartObjects\ChartObjectsTxtControls.mqh>
#include "TradeManagerDefines.mqh"
#include "RiskCalculator.mqh"
#include "VisualTradeTool.mqh"
#include "OrderExecution.mqh"

//+------------------------------------------------------------------+
//| CLASS: CTradeManagerGUI                                          |
//| Renders on-chart UI: Main Toolbar, Compact Mode, Trades, Exposure|
//+------------------------------------------------------------------+
class CTradeManagerGUI
{
private:
   long                 m_chart_id;
   int                  m_subwin;
   string               m_symbol;
   ENUM_THEME           m_theme;
   ENUM_PANEL_MODE      m_panel_mode;
   ENUM_PANEL_MODE      m_rendered_mode;
   bool                 m_show_trades_wnd;
   bool                 m_show_exposure_wnd;
   bool                 m_trades_drawn;
   bool                 m_exposure_drawn;
   bool                 m_hide_money;

   // UI Coordinates & Dimensions
   int                  m_x;
   int                  m_y;
   int                  m_width;
   int                  m_height;

   // Colors based on theme
   color                m_col_bg;
   color                m_col_panel;
   color                m_col_border;
   color                m_col_text_pri;
   color                m_col_text_sec;
   color                m_col_btn_buy;
   color                m_col_btn_sell;
   color                m_col_accent;
   color                m_col_highlight;

   // Helper: Format Money or mask
   string FormatMoney(double money, string prefix = "$")
   {
      if(m_hide_money)
         return prefix + "***";
      return prefix + DoubleToString(money, 2);
   }

   // GUI Object creation helpers
   bool CreateRect(string name, int x, int y, int w, int h, color bg_col, color border_col, bool selectable = false)
   {
      string obj_name = PREFIX_GUI + name;
      if(ObjectFind(m_chart_id, obj_name) < 0)
      {
         if(!ObjectCreate(m_chart_id, obj_name, OBJ_RECTANGLE_LABEL, m_subwin, 0, 0))
            return false;
      }
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_YDISTANCE, y);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_XSIZE, w);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_YSIZE, h);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_BGCOLOR, bg_col);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_BORDER_COLOR, border_col);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_BACK, false);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_SELECTABLE, selectable);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_SELECTED, false);
      return true;
   }

   bool CreateLabel(string name, int x, int y, string text, color text_col, int font_size = 9, string font = "Segoe UI")
   {
      string obj_name = PREFIX_GUI + name;
      if(ObjectFind(m_chart_id, obj_name) < 0)
      {
         if(!ObjectCreate(m_chart_id, obj_name, OBJ_LABEL, m_subwin, 0, 0))
            return false;
      }
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_YDISTANCE, y);
      ObjectSetString(m_chart_id, obj_name, OBJPROP_TEXT, text);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_COLOR, text_col);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_FONTSIZE, font_size);
      ObjectSetString(m_chart_id, obj_name, OBJPROP_FONT, font);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_SELECTABLE, false);
      return true;
   }

   bool CreateButton(string name, int x, int y, int w, int h, string text, color bg_col, color text_col, int font_size = 8)
   {
      string obj_name = PREFIX_GUI + name;
      if(ObjectFind(m_chart_id, obj_name) < 0)
      {
         if(!ObjectCreate(m_chart_id, obj_name, OBJ_BUTTON, m_subwin, 0, 0))
            return false;
      }
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_YDISTANCE, y);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_XSIZE, w);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_YSIZE, h);
      ObjectSetString(m_chart_id, obj_name, OBJPROP_TEXT, text);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_BGCOLOR, bg_col);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_COLOR, text_col);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_FONTSIZE, font_size);
      ObjectSetString(m_chart_id, obj_name, OBJPROP_FONT, "Segoe UI Bold");
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_STATE, false);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_SELECTABLE, false);
      return true;
   }

   bool CreateEdit(string name, int x, int y, int w, int h, string text, color bg_col, color text_col, int font_size = 9)
   {
      string obj_name = PREFIX_GUI + name;
      bool exists = (ObjectFind(m_chart_id, obj_name) >= 0);
      string cur_text = exists ? ObjectGetString(m_chart_id, obj_name, OBJPROP_TEXT) : "";
      if(!exists)
      {
         if(!ObjectCreate(m_chart_id, obj_name, OBJ_EDIT, m_subwin, 0, 0))
            return false;
      }
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_YDISTANCE, y);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_XSIZE, w);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_YSIZE, h);
      // Preserve in-progress typing: per-tick re-renders must not wipe the edit box.
      // Only overwrite when the numeric value actually changed.
      string cur_tmp = cur_text, new_tmp = text;
      StringReplace(cur_tmp, "%", ""); StringReplace(cur_tmp, "$", "");
      StringReplace(new_tmp, "%", ""); StringReplace(new_tmp, "$", "");
      if(!exists || MathAbs(StringToDouble(cur_tmp) - StringToDouble(new_tmp)) > 0.0000001)
         ObjectSetString(m_chart_id, obj_name, OBJPROP_TEXT, text);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_BGCOLOR, bg_col);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_COLOR, text_col);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_BORDER_COLOR, m_col_border);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_ALIGN, ALIGN_CENTER);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_FONTSIZE, font_size);
      ObjectSetString(m_chart_id, obj_name, OBJPROP_FONT, "Segoe UI Bold");
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(m_chart_id, obj_name, OBJPROP_READONLY, false);
      return true;
   }

public:
   CTradeManagerGUI(void)
   {
      m_chart_id          = 0;
      m_subwin            = 0;
      m_symbol            = _Symbol;
      m_theme             = THEME_DARK;
      m_panel_mode        = PANEL_MODE_FULL;
      m_rendered_mode     = (ENUM_PANEL_MODE)(-1);
      m_show_trades_wnd   = false;
      m_show_exposure_wnd = false;
      m_trades_drawn      = false;
      m_exposure_drawn    = false;
      m_hide_money        = false;

      m_x      = 25;
      m_y      = 35;
      m_width  = 260;
      m_height = 360;

      SetTheme(THEME_DARK);
   }

   ~CTradeManagerGUI(void)
   {
      DestroyAll();
   }

   //+------------------------------------------------------------------+
   //| Setup Theme                                                      |
   //+------------------------------------------------------------------+
   void SetTheme(ENUM_THEME theme)
   {
      m_theme = theme;
      if(m_theme == THEME_DARK)
      {
         m_col_bg        = CLR_DARK_BG;
         m_col_panel     = CLR_DARK_PANEL_BG;
         m_col_border    = CLR_DARK_BORDER;
         m_col_text_pri  = CLR_DARK_TEXT_PRIMARY;
         m_col_text_sec  = CLR_DARK_TEXT_SECONDARY;
         m_col_btn_buy   = CLR_DARK_BUY;
         m_col_btn_sell  = CLR_DARK_SELL;
         m_col_accent    = CLR_DARK_ACCENT;
         m_col_highlight = CLR_DARK_HIGHLIGHT;
      }
      else
      {
         m_col_bg        = CLR_LIGHT_BG;
         m_col_panel     = CLR_LIGHT_PANEL_BG;
         m_col_border    = CLR_LIGHT_BORDER;
         m_col_text_pri  = CLR_LIGHT_TEXT_PRIMARY;
         m_col_text_sec  = CLR_LIGHT_TEXT_SECONDARY;
         m_col_btn_buy   = CLR_LIGHT_BUY;
         m_col_btn_sell  = CLR_LIGHT_SELL;
         m_col_accent    = CLR_LIGHT_ACCENT;
         m_col_highlight = CLR_LIGHT_HIGHLIGHT;
      }
   }

   void Init(long chart_id, string symbol, ENUM_THEME theme, bool hide_money = false)
   {
      m_chart_id   = chart_id;
      m_symbol     = symbol;
      m_hide_money = hide_money;
      SetTheme(theme);
   }

   //+------------------------------------------------------------------+
   //| Render Main Panel Toolbar                                        |
   //+------------------------------------------------------------------+
   void RenderMainPanel(const STradePlan &plan, ENUM_RISK_MODE risk_mode, double risk_input_val)
   {
      // Panel mode changed: wipe stale mode-specific objects before redraw
      if(m_panel_mode != m_rendered_mode)
      {
         DestroyMainPanel();
         m_rendered_mode = m_panel_mode;
      }

      // If Minimized to logo only
      if(m_panel_mode == PANEL_MODE_MINIMIZED)
      {
         DestroyMainPanel();
         CreateRect("MINI_BG", m_x, m_y, 140, 26, m_col_bg, m_col_accent, true);
         CreateButton("BTN_LOGO", m_x + 2, m_y + 2, 100, 22, "TFX Manager", m_col_panel, m_col_accent, 8);
         CreateButton("BTN_MINIMIZE", m_x + 106, m_y + 2, 30, 22, "[+]", m_col_panel, m_col_text_pri, 8);
         ChartRedraw(m_chart_id);
         return;
      }

      int cur_h = (m_panel_mode == PANEL_MODE_COMPACT) ? 190 : m_height;

      // 1. Background Frames
      CreateRect("MAIN_BG", m_x, m_y, m_width, cur_h, m_col_bg, m_col_border);
      CreateRect("HEADER_BG", m_x + 1, m_y + 1, m_width - 2, 28, m_col_panel, m_col_border, true);

      // Header Bar
      CreateLabel("LBL_TITLE", m_x + 10, m_y + 6, "TFX Trade Manager", m_col_accent, 10, "Segoe UI Bold");
      CreateButton("BTN_MINIMIZE", m_x + m_width - 55, m_y + 4, 22, 20, (m_panel_mode == PANEL_MODE_COMPACT ? "[+]" : "[-]"), m_col_panel, m_col_text_sec, 8);
      CreateButton("BTN_CLOSE", m_x + m_width - 28, m_y + 4, 22, 20, "X", m_col_panel, m_col_btn_sell, 8);

      int cy = m_y + 34;

      // 2. Buy / Sell Toggle Buttons
      color buy_bg  = (plan.direction == TRADE_DIR_BUY)  ? m_col_btn_buy  : m_col_panel;
      color sell_bg = (plan.direction == TRADE_DIR_SELL) ? m_col_btn_sell : m_col_panel;
      CreateButton("BTN_DIR_BUY",  m_x + 8, cy, 118, 26, "BUY", buy_bg, clrWhite, 9);
      CreateButton("BTN_DIR_SELL", m_x + 134, cy, 118, 26, "SELL", sell_bg, clrWhite, 9);

      cy += 30;

      // 3. Order Type & Follow Price
      string ord_str = (plan.order_type == ORDER_EXEC_MARKET) ? "MARKET" : (plan.order_type == ORDER_EXEC_LIMIT ? "LIMIT" : "STOP");
      CreateButton("BTN_ORD_TYPE", m_x + 8, cy, 118, 22, ord_str, m_col_panel, m_col_text_pri, 8);

      string follow_str = plan.follow_price ? "Follow: ON" : "Follow: OFF";
      color follow_col = plan.follow_price ? m_col_accent : m_col_text_sec;
      CreateButton("BTN_FOLLOW_PRICE", m_x + 134, cy, 118, 22, follow_str, m_col_panel, follow_col, 8);

      cy += 28;

      // 4. Risk Mode & Input Field
      string risk_mode_str = (risk_mode == RISK_MODE_PERCENT) ? "Risk %" : (risk_mode == RISK_MODE_MONEY ? "Risk $" : "Fixed Lot");
      CreateButton("BTN_RISK_MODE", m_x + 8, cy, 80, 22, risk_mode_str, m_col_panel, m_col_highlight, 8);

      string input_str = (risk_mode == RISK_MODE_PERCENT) ? DoubleToString(risk_input_val, 1) + "%" :
                         (risk_mode == RISK_MODE_MONEY)   ? FormatMoney(risk_input_val, "$") :
                         DoubleToString(risk_input_val, 2);
      CreateEdit("EDIT_RISK_VAL", m_x + 92, cy, 80, 22, input_str, m_col_panel, m_col_text_pri, 9);

      // Quick Risk buttons
      CreateButton("BTN_RISK_P1", m_x + 176, cy, 36, 22, "1%", m_col_panel, m_col_text_pri, 7);
      CreateButton("BTN_RISK_P2", m_x + 216, cy, 36, 22, "2%", m_col_panel, m_col_text_pri, 7);

      cy += 28;

      // If in compact mode, render execute button right here
      if(m_panel_mode == PANEL_MODE_COMPACT)
      {
         string exec_txt = StringFormat("EXECUTE %s  (%.2f Lots)", (plan.direction == TRADE_DIR_BUY ? "BUY" : "SELL"), plan.total_lots);
         color exec_bg = (plan.direction == TRADE_DIR_BUY) ? m_col_btn_buy : m_col_btn_sell;
         CreateButton("BTN_EXECUTE", m_x + 8, cy, m_width - 16, 32, exec_txt, exec_bg, clrWhite, 10);

         cy += 36;
         string mini_stat = StringFormat("Risk: %s | Pips: %.1f", FormatMoney(plan.risk_money), plan.sl_distance_pips);
         CreateLabel("LBL_MINI_STAT", m_x + 10, cy, mini_stat, m_col_text_sec, 8);
         ChartRedraw(m_chart_id);
         return;
      }

      // 5. Targets (1, 2, 3) & Lock R:R
      color t1_col = (plan.num_targets == 1) ? m_col_accent : m_col_panel;
      color t2_col = (plan.num_targets == 2) ? m_col_accent : m_col_panel;
      color t3_col = (plan.num_targets == 3) ? m_col_accent : m_col_panel;

      CreateButton("BTN_TARGET_1", m_x + 8,  cy, 38, 22, "1 TP", t1_col, clrWhite, 8);
      CreateButton("BTN_TARGET_2", m_x + 50, cy, 38, 22, "2 TP", t2_col, clrWhite, 8);
      CreateButton("BTN_TARGET_3", m_x + 92, cy, 38, 22, "3 TP", t3_col, clrWhite, 8);

      string lock_str = plan.lock_rr ? "Lock RR: ON" : "Lock RR: OFF";
      color lock_bg = plan.lock_rr ? m_col_accent : m_col_panel;
      CreateButton("BTN_LOCK_RR", m_x + 138, cy, 114, 22, lock_str, lock_bg, clrWhite, 8);

      cy += 28;

      // 6. Statistics Box
      CreateRect("STAT_FRAME", m_x + 8, cy, m_width - 16, 84, m_col_panel, m_col_border);

      string s_vol  = StringFormat("Total Volume:  %.2f Lots", plan.total_lots);
      string s_risk = StringFormat("Risk Loss:    -%s (%.2f%%) | %.1f pips",
                                   FormatMoney(plan.risk_money), plan.risk_percent, plan.sl_distance_pips);
      string s_prof = StringFormat("Profit Est:   +%s | Avg RR: 1:%.2f",
                                   FormatMoney(plan.total_reward_money), plan.avg_rr_ratio);
      
      string s_split = "Split: ";
      for(int i = 0; i < plan.num_targets; i++)
         s_split += StringFormat("T%d: %.2f ", i + 1, plan.target_lots[i]);

      CreateLabel("LBL_STAT_VOL",   m_x + 14, cy + 6,  s_vol,   m_col_highlight, 9, "Segoe UI Bold");
      CreateLabel("LBL_STAT_RISK",  m_x + 14, cy + 24, s_risk,  m_col_btn_sell,  8);
      CreateLabel("LBL_STAT_PROF",  m_x + 14, cy + 42, s_prof,  m_col_btn_buy,   8);
      CreateLabel("LBL_STAT_SPLIT", m_x + 14, cy + 60, s_split, m_col_text_sec,  8);

      cy += 92;

      // 7. Big One-Click Order Button
      string exec_txt = StringFormat("EXECUTE %s  (%.2f Lots)", (plan.direction == TRADE_DIR_BUY ? "BUY" : "SELL"), plan.total_lots);
      color exec_bg = (plan.direction == TRADE_DIR_BUY) ? m_col_btn_buy : m_col_btn_sell;
      CreateButton("BTN_EXECUTE", m_x + 8, cy, m_width - 16, 34, exec_txt, exec_bg, clrWhite, 10);

      cy += 38;

      // 8. Management Navigation Row
      color trd_bg = m_show_trades_wnd ? m_col_accent : m_col_panel;
      color exp_bg = m_show_exposure_wnd ? m_col_accent : m_col_panel;
      CreateButton("BTN_NAV_TRADES",   m_x + 8, cy, 118, 22, "Manage Trades", trd_bg, clrWhite, 8);
      CreateButton("BTN_NAV_EXPOSURE", m_x + 134, cy, 118, 22, "Account Exposure", exp_bg, clrWhite, 8);

      ChartRedraw(m_chart_id);
   }

   //+------------------------------------------------------------------+
   //| Render Trades Management Popup Window (Shift + M)                |
   //+------------------------------------------------------------------+
   void RenderTradesWindow(COrderExecution &exec)
   {
      if(!m_show_trades_wnd)
      {
         if(m_trades_drawn)
         {
            DestroyTradesWindow();
            m_trades_drawn = false;
         }
         return;
      }

      int wx = m_x + m_width + 10;
      int wy = m_y;
      int ww = 320;
      int wh = 240;

      CreateRect("TRD_BG", wx, wy, ww, wh, m_col_bg, m_col_border);
      CreateRect("TRD_HEADER", wx + 1, wy + 1, ww - 2, 28, m_col_panel, m_col_border);
      CreateLabel("TRD_TITLE", wx + 10, wy + 6, "Live Trades Management", m_col_accent, 10, "Segoe UI Bold");
      CreateButton("TRD_BTN_CLOSE", wx + ww - 28, wy + 4, 22, 20, "X", m_col_panel, m_col_btn_sell, 8);

      // Bulk Action Buttons
      int by = wy + 35;
      CreateButton("TRD_CLOSE_ALL",   wx + 10, by, 145, 26, "Close All Trades", m_col_btn_sell, clrWhite, 8);
      CreateButton("TRD_CLOSE_PROF",  wx + 165, by, 145, 26, "Close In Profit", m_col_btn_buy, clrWhite, 8);

      by += 32;
      CreateButton("TRD_CLOSE_LOSS",  wx + 10, by, 145, 26, "Close In Loss", m_col_panel, m_col_text_pri, 8);
      CreateButton("TRD_PARTIAL_50", wx + 165, by, 145, 26, "Partial Close 50%", m_col_panel, m_col_highlight, 8);

      by += 32;
      CreateButton("TRD_BE_ALL",      wx + 10, by, ww - 20, 26, "Move All To Break-Even", m_col_panel, m_col_accent, 8);

      by += 34;
      // Position statistics
      int pos_count = PositionsTotal();
      double total_vol = 0.0;
      double total_pnl = 0.0;

      for(int i = 0; i < pos_count; i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket > 0)
         {
            total_vol += PositionGetDouble(POSITION_VOLUME);
            total_pnl += PositionGetDouble(POSITION_PROFIT);
         }
      }

      CreateRect("TRD_STAT_BOX", wx + 10, by, ww - 20, 68, m_col_panel, m_col_border);
      CreateLabel("TRD_LBL_CNT", wx + 16, by + 8,  StringFormat("Open Positions:   %d", pos_count), m_col_text_pri, 8);
      CreateLabel("TRD_LBL_VOL", wx + 16, by + 26, StringFormat("Total Traded Lots: %.2f", total_vol), m_col_highlight, 8);
      
      color pnl_col = (total_pnl >= 0.0) ? m_col_btn_buy : m_col_btn_sell;
      string pnl_str = StringFormat("Floating Profit:  %s%s", (total_pnl >= 0 ? "+" : ""), FormatMoney(total_pnl));
      CreateLabel("TRD_LBL_PNL", wx + 16, by + 44, pnl_str, pnl_col, 9, "Segoe UI Bold");

      m_trades_drawn = true;
      ChartRedraw(m_chart_id);
   }

   //+------------------------------------------------------------------+
   //| Render Account Exposure Window (Shift + X)                       |
   //+------------------------------------------------------------------+
   void RenderExposureWindow(void)
   {
      if(!m_show_exposure_wnd)
      {
         if(m_exposure_drawn)
         {
            DestroyExposureWindow();
            m_exposure_drawn = false;
         }
         return;
      }

      int wx = m_x + m_width + 10;
      int wy = m_y + (m_show_trades_wnd ? 250 : 0);
      int ww = 320;
      int wh = 300;

      CreateRect("EXP_BG", wx, wy, ww, wh, m_col_bg, m_col_border);
      CreateRect("EXP_HEADER", wx + 1, wy + 1, ww - 2, 28, m_col_panel, m_col_border);
      CreateLabel("EXP_TITLE", wx + 10, wy + 6, "Account Exposure & Risk", m_col_accent, 10, "Segoe UI Bold");
      CreateButton("EXP_BTN_CLOSE", wx + ww - 28, wy + 4, 22, 20, "X", m_col_panel, m_col_btn_sell, 8);

      double bal   = AccountInfoDouble(ACCOUNT_BALANCE);
      double eq    = AccountInfoDouble(ACCOUNT_EQUITY);
      double margin = AccountInfoDouble(ACCOUNT_MARGIN);
      double free_m = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      double m_lvl = (margin > 0.0) ? (eq / margin) * 100.0 : 0.0;

      int ly = wy + 36;
      CreateLabel("EXP_LBL_BAL",  wx + 16, ly,      StringFormat("Account Balance: %s", FormatMoney(bal)), m_col_text_pri, 8);
      CreateLabel("EXP_LBL_EQ",   wx + 16, ly + 20, StringFormat("Equity:          %s", FormatMoney(eq)), m_col_text_pri, 8);
      CreateLabel("EXP_LBL_MAR",  wx + 16, ly + 40, StringFormat("Used Margin:     %s", FormatMoney(margin)), m_col_text_sec, 8);
      CreateLabel("EXP_LBL_FREE", wx + 16, ly + 60, StringFormat("Free Margin:     %s", FormatMoney(free_m)), m_col_text_sec, 8);
      CreateLabel("EXP_LBL_LVL",  wx + 16, ly + 80, StringFormat("Margin Level:    %.2f%%", m_lvl), m_col_highlight, 8);

      // Current Chart Symbol Net Exposure
      double sym_buy = 0.0, sym_sell = 0.0;
      for(int i = 0; i < PositionsTotal(); i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket > 0 && PositionGetString(POSITION_SYMBOL) == m_symbol)
         {
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
               sym_buy += PositionGetDouble(POSITION_VOLUME);
            else
               sym_sell += PositionGetDouble(POSITION_VOLUME);
         }
      }
      double net_exp = sym_buy - sym_sell;
      color net_col = (net_exp > 0) ? m_col_btn_buy : (net_exp < 0 ? m_col_btn_sell : m_col_text_sec);
      string net_sign = (net_exp >= 0.0) ? "+" : "";
      string exp_str = StringFormat("%s Net: %s%.2f Lots (L: %.2f / S: %.2f)",
                                    m_symbol, net_sign, net_exp, sym_buy, sym_sell);
      CreateLabel("EXP_LBL_SYM", wx + 16, ly + 110, exp_str, net_col, 9, "Segoe UI Bold");

      // Per-Symbol Exposure Breakdown (all open symbols, top 5 by listing order)
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "EXP_SYM_");
      string agg_syms[];
      double agg_buy[], agg_sell[];
      for(int i = 0; i < PositionsTotal(); i++)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket <= 0)
            continue;
         string ps = PositionGetString(POSITION_SYMBOL);
         double pv = PositionGetDouble(POSITION_VOLUME);
         bool is_buy = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
         int si = -1;
         for(int k = 0; k < ArraySize(agg_syms); k++)
         {
            if(agg_syms[k] == ps) { si = k; break; }
         }
         if(si < 0)
         {
            si = ArraySize(agg_syms);
            ArrayResize(agg_syms, si + 1);
            ArrayResize(agg_buy, si + 1);
            ArrayResize(agg_sell, si + 1);
            agg_syms[si] = ps;
         }
         if(is_buy)
            agg_buy[si] += pv;
         else
            agg_sell[si] += pv;
      }
      int exp_rows = MathMin(ArraySize(agg_syms), 5);
      for(int r = 0; r < exp_rows; r++)
      {
         double net_r = agg_buy[r] - agg_sell[r];
         color rc = (net_r > 0) ? m_col_btn_buy : (net_r < 0 ? m_col_btn_sell : m_col_text_sec);
         string rsign = (net_r >= 0.0) ? "+" : "";
         string row_txt = StringFormat("%s: %s%.2f (L %.2f / S %.2f)", agg_syms[r], rsign, net_r, agg_buy[r], agg_sell[r]);
         CreateLabel("EXP_SYM_" + IntegerToString(r), wx + 16, ly + 132 + r * 18, row_txt, rc, 8);
      }
      if(ArraySize(agg_syms) > 5)
         CreateLabel("EXP_SYM_MORE", wx + 16, ly + 132 + 5 * 18, StringFormat("+%d more symbols...", ArraySize(agg_syms) - 5), m_col_text_sec, 8);

      m_exposure_drawn = true;
      ChartRedraw(m_chart_id);
   }

   //+------------------------------------------------------------------+
   //| Handle GUI clicks and inputs                                     |
   //+------------------------------------------------------------------+
   bool HandleChartEvent(const int id,
                         const long &lparam,
                         const double &dparam,
                         const string &sparam,
                         STradePlan &plan,
                         ENUM_RISK_MODE &risk_mode,
                         double &risk_input_val,
                         COrderExecution &exec,
                         CVisualTradeTool &visual)
   {
      // 0. Panel dragging (movable windows): header drag re-anchors the whole panel
      if(id == CHARTEVENT_OBJECT_DRAG)
      {
         if(sparam == PREFIX_GUI + "HEADER_BG" || sparam == PREFIX_GUI + "MINI_BG")
         {
            int nx = (int)ObjectGetInteger(m_chart_id, sparam, OBJPROP_XDISTANCE);
            int ny = (int)ObjectGetInteger(m_chart_id, sparam, OBJPROP_YDISTANCE);
            int cw = (int)ChartGetInteger(m_chart_id, CHART_WIDTH_IN_PIXELS);
            int ch = (int)ChartGetInteger(m_chart_id, CHART_HEIGHT_IN_PIXELS);
            int hdr_off = (sparam == PREFIX_GUI + "HEADER_BG") ? 1 : 0;
            m_x = MathMax(0, MathMin(nx - hdr_off, MathMax(0, cw - 60)));
            m_y = MathMax(0, MathMin(ny - hdr_off, MathMax(0, ch - 60)));
            ObjectSetInteger(m_chart_id, sparam, OBJPROP_SELECTED, false);
            return true; // main EA re-renders everything at the new anchor
         }
         return false;
      }

      // 1. Button Clicks
      if(id == CHARTEVENT_OBJECT_CLICK)
      {
         // Minimize / Expand
         if(sparam == PREFIX_GUI + "BTN_MINIMIZE")
         {
            if(m_panel_mode == PANEL_MODE_FULL)
               m_panel_mode = PANEL_MODE_COMPACT;
            else if(m_panel_mode == PANEL_MODE_COMPACT)
               m_panel_mode = PANEL_MODE_MINIMIZED;
            else
               m_panel_mode = PANEL_MODE_FULL;

            DestroyAll();
            return true;
         }

         if(sparam == PREFIX_GUI + "BTN_LOGO")
         {
            m_panel_mode = PANEL_MODE_FULL;
            DestroyAll();
            return true;
         }

         // Close / Hide
         if(sparam == PREFIX_GUI + "BTN_CLOSE")
         {
            m_panel_mode = PANEL_MODE_MINIMIZED;
            DestroyAll();
            return true;
         }

         // Direction Toggle
         if(sparam == PREFIX_GUI + "BTN_DIR_BUY")
         {
            plan.direction = TRADE_DIR_BUY;
            // Place SL below Entry, and TPs above Entry
            double sl_dist = MathAbs(plan.entry_price - plan.sl_price);
            if(sl_dist <= 0.0) sl_dist = 300 * _Point;
            plan.sl_price = plan.entry_price - sl_dist;
            for(int i = 0; i < plan.num_targets; i++)
               plan.tp_prices[i] = plan.entry_price + sl_dist * (i + 1) * 1.5;
            return true;
         }

         if(sparam == PREFIX_GUI + "BTN_DIR_SELL")
         {
            plan.direction = TRADE_DIR_SELL;
            double sl_dist = MathAbs(plan.entry_price - plan.sl_price);
            if(sl_dist <= 0.0) sl_dist = 300 * _Point;
            plan.sl_price = plan.entry_price + sl_dist;
            for(int i = 0; i < plan.num_targets; i++)
               plan.tp_prices[i] = plan.entry_price - sl_dist * (i + 1) * 1.5;
            return true;
         }

         // Order Type
         if(sparam == PREFIX_GUI + "BTN_ORD_TYPE")
         {
            if(plan.order_type == ORDER_EXEC_MARKET)
               plan.order_type = ORDER_EXEC_LIMIT;
            else if(plan.order_type == ORDER_EXEC_LIMIT)
               plan.order_type = ORDER_EXEC_STOP;
            else
               plan.order_type = ORDER_EXEC_MARKET;
            return true;
         }

         // Follow Price Toggle
         if(sparam == PREFIX_GUI + "BTN_FOLLOW_PRICE")
         {
            plan.follow_price = !plan.follow_price;
            return true;
         }

         // Risk Mode Toggle
         if(sparam == PREFIX_GUI + "BTN_RISK_MODE")
         {
            if(risk_mode == RISK_MODE_PERCENT)
            {
               risk_mode = RISK_MODE_MONEY;
               risk_input_val = 100.0;
            }
            else if(risk_mode == RISK_MODE_MONEY)
            {
               risk_mode = RISK_MODE_FIXED_LOT;
               risk_input_val = 0.50;
            }
            else
            {
               risk_mode = RISK_MODE_PERCENT;
               risk_input_val = 1.0;
            }
            return true;
         }

         // Quick Risk Presets
         if(sparam == PREFIX_GUI + "BTN_RISK_P1")
         {
            risk_mode = RISK_MODE_PERCENT;
            risk_input_val = 1.0;
            return true;
         }
         if(sparam == PREFIX_GUI + "BTN_RISK_P2")
         {
            risk_mode = RISK_MODE_PERCENT;
            risk_input_val = 2.0;
            return true;
         }

         // Target Count
         if(sparam == PREFIX_GUI + "BTN_TARGET_1") { plan.num_targets = 1; return true; }
         if(sparam == PREFIX_GUI + "BTN_TARGET_2") { plan.num_targets = 2; return true; }
         if(sparam == PREFIX_GUI + "BTN_TARGET_3") { plan.num_targets = 3; return true; }

         // Lock RR Toggle
         if(sparam == PREFIX_GUI + "BTN_LOCK_RR")
         {
            plan.lock_rr = !plan.lock_rr;
            return true;
         }

         // EXECUTE ORDER
         if(sparam == PREFIX_GUI + "BTN_EXECUTE")
         {
            exec.ExecutePlan(plan);
            return true;
         }

         // Windows Navigation
         if(sparam == PREFIX_GUI + "BTN_NAV_TRADES")
         {
            m_show_trades_wnd = !m_show_trades_wnd;
            return true;
         }
         if(sparam == PREFIX_GUI + "BTN_NAV_EXPOSURE")
         {
            m_show_exposure_wnd = !m_show_exposure_wnd;
            return true;
         }

         // Window Close buttons
         if(sparam == PREFIX_GUI + "TRD_BTN_CLOSE")
         {
            m_show_trades_wnd = false;
            DestroyTradesWindow();
            return true;
         }
         if(sparam == PREFIX_GUI + "EXP_BTN_CLOSE")
         {
            m_show_exposure_wnd = false;
            DestroyExposureWindow();
            return true;
         }

         // Trades Window Action Buttons
         if(sparam == PREFIX_GUI + "TRD_CLOSE_ALL")
         {
            exec.CloseAllPositions(m_symbol);
            return true;
         }
         if(sparam == PREFIX_GUI + "TRD_CLOSE_PROF")
         {
            exec.CloseProfitablePositions(m_symbol);
            return true;
         }
         if(sparam == PREFIX_GUI + "TRD_CLOSE_LOSS")
         {
            exec.CloseLosingPositions(m_symbol);
            return true;
         }
         if(sparam == PREFIX_GUI + "TRD_PARTIAL_50")
         {
            exec.PartialClosePositions(50.0, m_symbol);
            return true;
         }
         if(sparam == PREFIX_GUI + "TRD_BE_ALL")
         {
            exec.BreakEvenAllPositions(m_symbol);
            return true;
         }
      }

      // 2. Edit Box changes
      if(id == CHARTEVENT_OBJECT_ENDEDIT)
      {
         if(sparam == PREFIX_GUI + "EDIT_RISK_VAL")
         {
            string str_val = ObjectGetString(m_chart_id, PREFIX_GUI + "EDIT_RISK_VAL", OBJPROP_TEXT);
            StringReplace(str_val, "%", "");
            StringReplace(str_val, "$", "");
            StringTrimLeft(str_val);
            StringTrimRight(str_val);
            double val = StringToDouble(str_val);
            if(val > 0.0)
            {
               risk_input_val = val;
               return true;
            }
         }
      }

      return false;
   }

   //+------------------------------------------------------------------+
   //| Cleanup Functions                                                |
   //+------------------------------------------------------------------+
   void DestroyMainPanel(void)
   {
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "MAIN_");
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "HEADER_");
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "LBL_");
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "BTN_");
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "EDIT_");
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "STAT_");
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "MINI_");
   }

   void DestroyTradesWindow(void)
   {
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "TRD_");
   }

   void DestroyExposureWindow(void)
   {
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI + "EXP_");
   }

   void DestroyAll(void)
   {
      ObjectsDeleteAll(m_chart_id, PREFIX_GUI);
      ChartRedraw(m_chart_id);
   }

   // Hide popups (Esc key): close windows without toggling them back on
   void HidePopups(void)
   {
      m_show_trades_wnd = false;
      m_show_exposure_wnd = false;
      DestroyTradesWindow();
      DestroyExposureWindow();
      m_trades_drawn = false;
      m_exposure_drawn = false;
      ChartRedraw(m_chart_id);
   }

   // Toggles
   void ToggleTradesWindow(void)   { m_show_trades_wnd = !m_show_trades_wnd; }
   void ToggleExposureWindow(void) { m_show_exposure_wnd = !m_show_exposure_wnd; }
   void ToggleCompactMode(void)
   {
      m_panel_mode = (m_panel_mode == PANEL_MODE_FULL) ? PANEL_MODE_COMPACT : PANEL_MODE_FULL;
      DestroyAll();
   }
   void SetPanelMode(ENUM_PANEL_MODE mode)
   {
      m_panel_mode = mode;
      DestroyAll();
   }
   ENUM_PANEL_MODE GetPanelMode(void) const { return m_panel_mode; }
};

