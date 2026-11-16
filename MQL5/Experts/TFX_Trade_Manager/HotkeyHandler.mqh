//+------------------------------------------------------------------+
//|                                                HotkeyHandler.mqh |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, ToolsFX"
#property link      "https://www.toolsfx.com"
#property strict

#include "TradeManagerDefines.mqh"
#include "VisualTradeTool.mqh"
#include "TradeManagerGUI.mqh"
#include "OrderExecution.mqh"

// Virtual key codes
#define VK_KEY_ESC       27
#define VK_KEY_1         49
#define VK_KEY_2         50
#define VK_KEY_3         51
#define VK_KEY_NUMPAD1   97
#define VK_KEY_NUMPAD2   98
#define VK_KEY_NUMPAD3   99
#define VK_KEY_E         69
#define VK_KEY_M         77
#define VK_KEY_X         88

//+------------------------------------------------------------------+
//| CLASS: CHotkeyHandler                                            |
//| Handles all keyboard shortcuts for one-click trading operations  |
//+------------------------------------------------------------------+
class CHotkeyHandler
{
public:
   //+------------------------------------------------------------------+
   //| Process Chart Key Down Event                                     |
   //+------------------------------------------------------------------+
   static bool ProcessKeyEvent(const int id,
                               const long &lparam,
                               const double &dparam,
                               const string &sparam,
                               STradePlan &plan,
                               CVisualTradeTool &visual,
                               CTradeManagerGUI &gui,
                               COrderExecution &exec)
   {
      if(id != CHARTEVENT_KEYDOWN)
         return false;

      int key = (int)lparam;

      bool is_shift = (TerminalInfoInteger(TERMINAL_KEYSTATE_SHIFT) < 0);
      bool is_ctrl  = (TerminalInfoInteger(TERMINAL_KEYSTATE_CONTROL) < 0);

      // 1. Shift + Esc: Toggle Buy / Sell mode
      if(key == VK_KEY_ESC && is_shift)
      {
         plan.direction = (plan.direction == TRADE_DIR_BUY) ? TRADE_DIR_SELL : TRADE_DIR_BUY;
         double sl_dist = MathAbs(plan.entry_price - plan.sl_price);
         if(sl_dist <= 0.0) sl_dist = 300 * _Point;

         if(plan.direction == TRADE_DIR_BUY)
         {
            plan.sl_price = plan.entry_price - sl_dist;
            for(int i = 0; i < plan.num_targets; i++)
               plan.tp_prices[i] = plan.entry_price + sl_dist * (i + 1) * 1.5;
         }
         else
         {
            plan.sl_price = plan.entry_price + sl_dist;
            for(int i = 0; i < plan.num_targets; i++)
               plan.tp_prices[i] = plan.entry_price - sl_dist * (i + 1) * 1.5;
         }
         Print("TFX Hotkey: Switched direction to ", (plan.direction == TRADE_DIR_BUY ? "BUY" : "SELL"));
         return true;
      }

      // 2. Esc: Show/Hide Tool or close popups
      if(key == VK_KEY_ESC && !is_shift)
      {
         visual.ToggleVisibility(plan);
         Print("TFX Hotkey: Toggled Visual Lines visibility");
         return true;
      }

      // 3. Ctrl + 1: Set Targets to 1
      if((key == VK_KEY_1 || key == VK_KEY_NUMPAD1) && is_ctrl)
      {
         plan.num_targets = 1;
         Print("TFX Hotkey: Set Targets to 1");
         return true;
      }

      // 4. Ctrl + 2: Set Targets to 2
      if((key == VK_KEY_2 || key == VK_KEY_NUMPAD2) && is_ctrl)
      {
         plan.num_targets = 2;
         Print("TFX Hotkey: Set Targets to 2");
         return true;
      }

      // 5. Ctrl + 3: Set Targets to 3
      if((key == VK_KEY_3 || key == VK_KEY_NUMPAD3) && is_ctrl)
      {
         plan.num_targets = 3;
         Print("TFX Hotkey: Set Targets to 3");
         return true;
      }

      // 6. Shift + E: Execute Order
      if((key == VK_KEY_E) && is_shift)
      {
         Print("TFX Hotkey: Shift + E pressed -> Executing Order!");
         exec.ExecutePlan(plan);
         return true;
      }

      // 7. Shift + M: Toggle Manage Trades window
      if((key == VK_KEY_M) && is_shift)
      {
         gui.ToggleTradesWindow();
         Print("TFX Hotkey: Toggled Manage Trades window");
         return true;
      }

      // 8. Shift + X: Toggle Account Exposure window
      if((key == VK_KEY_X) && is_shift)
      {
         gui.ToggleExposureWindow();
         Print("TFX Hotkey: Toggled Account Exposure window");
         return true;
      }

      return false;
   }
};

