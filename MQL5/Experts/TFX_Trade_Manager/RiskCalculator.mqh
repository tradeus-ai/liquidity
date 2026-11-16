//+------------------------------------------------------------------+
//|                                               RiskCalculator.mqh |
//|                             Copyright 2026, TFX Trade Manager EA |
//|                                         https://www.toolsfx.com/ |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, ToolsFX"
#property link      "https://www.toolsfx.com"
#property strict

#include "TradeManagerDefines.mqh"

//+------------------------------------------------------------------+
//| CLASS: CRiskCalculator                                           |
//| Handles multi-asset position sizing, margin, and risk/reward     |
//+------------------------------------------------------------------+
class CRiskCalculator
{
private:
   string               m_symbol;
   int                  m_digits;
   double               m_point;
   double               m_tick_size;
   double               m_tick_val_loss;
   double               m_tick_val_profit;
   double               m_vol_min;
   double               m_vol_max;
   double               m_vol_step;
   int                  m_lot_digits;
   double               m_contract_size;

   // Helper to count decimals in lot step
   int GetLotStepDecimals(double step)
   {
      int dec = 0;
      double s = step;
      while(s < 1.0 && dec < 8)
      {
         s *= 10.0;
         dec++;
      }
      return dec;
   }

public:
   CRiskCalculator(void)
   {
      m_symbol = "";
      m_digits = 0;
      m_point = 0.0;
      m_tick_size = 0.0;
      m_tick_val_loss = 0.0;
      m_tick_val_profit = 0.0;
      m_vol_min = 0.01;
      m_vol_max = 100.0;
      m_vol_step = 0.01;
      m_lot_digits = 2;
      m_contract_size = 100000.0;
   }

   //+------------------------------------------------------------------+
   //| Initialize or refresh symbol parameters                          |
   //+------------------------------------------------------------------+
   bool InitSymbol(string symbol)
   {
      m_symbol = (symbol == "" || symbol == NULL) ? _Symbol : symbol;
      
      if(!SymbolInfoInteger(m_symbol, SYMBOL_DIGITS, m_digits))
         m_digits = _Digits;
      if(!SymbolInfoDouble(m_symbol, SYMBOL_POINT, m_point))
         m_point = _Point;
      if(!SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_SIZE, m_tick_size))
         m_tick_size = m_point;
      if(m_tick_size <= 0.0)
         m_tick_size = m_point;

      if(!SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_VALUE_LOSS, m_tick_val_loss))
         m_tick_val_loss = 1.0;
      if(!SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_VALUE_PROFIT, m_tick_val_profit))
         m_tick_val_profit = m_tick_val_loss;

      if(!SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN, m_vol_min))
         m_vol_min = 0.01;
      if(!SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX, m_vol_max))
         m_vol_max = 100.0;
      if(!SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP, m_vol_step))
         m_vol_step = 0.01;

      m_lot_digits = GetLotStepDecimals(m_vol_step);

      if(!SymbolInfoDouble(m_symbol, SYMBOL_TRADE_CONTRACT_SIZE, m_contract_size))
         m_contract_size = 100000.0;

      return true;
   }

   //+------------------------------------------------------------------+
   //| Normalize lot size to broker step and clamp to min/max           |
   //+------------------------------------------------------------------+
   double NormalizeLots(double raw_lots)
   {
      if(raw_lots <= 0.0)
         return 0.0;

      double steps = MathFloor(raw_lots / m_vol_step + 0.0000001);
      double lots = steps * m_vol_step;

      lots = NormalizeDouble(lots, m_lot_digits);

      if(lots < m_vol_min)
         lots = m_vol_min;
      if(lots > m_vol_max)
         lots = m_vol_max;

      return NormalizeDouble(lots, m_lot_digits);
   }

   //+------------------------------------------------------------------+
   //| Get base equity/balance value                                    |
   //+------------------------------------------------------------------+
   double GetAccountBase(ENUM_ACCOUNT_BASE base_type)
   {
      switch(base_type)
      {
         case ACCOUNT_BASE_BALANCE:
            return AccountInfoDouble(ACCOUNT_BALANCE);
         case ACCOUNT_BASE_EQUITY:
            return AccountInfoDouble(ACCOUNT_EQUITY);
         case ACCOUNT_BASE_FREE_MARGIN:
            return AccountInfoDouble(ACCOUNT_MARGIN_FREE);
         default:
            return AccountInfoDouble(ACCOUNT_BALANCE);
      }
   }

   //+------------------------------------------------------------------+
   //| Calculate monetary loss per 1.0 lot from Entry to SL             |
   //+------------------------------------------------------------------+
   double CalculateLossPerLot(ENUM_TRADE_DIR dir, double entry, double sl)
   {
      if(entry <= 0.0 || sl <= 0.0)
         return 0.0;

      ENUM_ORDER_TYPE ot = (dir == TRADE_DIR_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      double loss_1_lot = 0.0;

      // 1. Try MT5 native OrderCalcProfit for maximum broker accuracy
      ResetLastError();
      if(OrderCalcProfit(ot, m_symbol, 1.0, entry, sl, loss_1_lot))
      {
         loss_1_lot = MathAbs(loss_1_lot);
         if(loss_1_lot > 0.000001)
            return loss_1_lot;
      }

      // 2. High-precision fallback via tick distance & tick value
      double price_diff = MathAbs(entry - sl);
      if(m_tick_size > 0.0 && m_tick_val_loss > 0.0)
      {
         double ticks = price_diff / m_tick_size;
         loss_1_lot = ticks * m_tick_val_loss;
         return MathAbs(loss_1_lot);
      }

      // 3. Fallback via point
      if(m_point > 0.0)
      {
         double points = price_diff / m_point;
         return points * (m_tick_val_loss > 0 ? m_tick_val_loss : 1.0);
      }

      return 0.0;
   }

   //+------------------------------------------------------------------+
   //| Calculate monetary profit per 1.0 lot from Entry to TP           |
   //+------------------------------------------------------------------+
   double CalculateProfitPerLot(ENUM_TRADE_DIR dir, double entry, double tp)
   {
      if(entry <= 0.0 || tp <= 0.0)
         return 0.0;

      ENUM_ORDER_TYPE ot = (dir == TRADE_DIR_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      double profit_1_lot = 0.0;

      ResetLastError();
      if(OrderCalcProfit(ot, m_symbol, 1.0, entry, tp, profit_1_lot))
      {
         profit_1_lot = MathAbs(profit_1_lot);
         if(profit_1_lot > 0.000001)
            return profit_1_lot;
      }

      double price_diff = MathAbs(tp - entry);
      if(m_tick_size > 0.0 && m_tick_val_profit > 0.0)
      {
         double ticks = price_diff / m_tick_size;
         profit_1_lot = ticks * m_tick_val_profit;
         return MathAbs(profit_1_lot);
      }

      return 0.0;
   }

   //+------------------------------------------------------------------+
   //| Core position sizing & trade plan engine                         |
   //+------------------------------------------------------------------+
   bool CalculatePlan(STradePlan &plan,
                      ENUM_RISK_MODE risk_mode,
                      double risk_input_value,
                      ENUM_ACCOUNT_BASE acc_base)
   {
      InitSymbol(m_symbol);

      if(plan.entry_price <= 0.0 || plan.sl_price <= 0.0)
         return false;

      // 1. Determine direction from Entry vs SL
      if(plan.entry_price > plan.sl_price)
         plan.direction = TRADE_DIR_BUY;
      else if(plan.entry_price < plan.sl_price)
         plan.direction = TRADE_DIR_SELL;
      else
         return false; // Entry equals SL

      // 2. SL distance
      double sl_diff = MathAbs(plan.entry_price - plan.sl_price);
      plan.sl_distance_points = (m_point > 0.0) ? NormalizeDouble(sl_diff / m_point, 1) : 0.0;
      plan.sl_distance_pips   = (m_point > 0.0) ? NormalizeDouble(sl_diff / (m_point * 10.0), 1) : 0.0;

      // 3. Loss per 1.0 lot
      double loss_1_lot = CalculateLossPerLot(plan.direction, plan.entry_price, plan.sl_price);
      if(loss_1_lot <= 0.000001)
         return false;

      // 4. Determine cash risk amount & total lots based on Risk Mode
      double account_funds = GetAccountBase(acc_base);
      if(account_funds <= 0.0)
         account_funds = 10000.0; // Fallback demo buffer

      double calculated_lots = 0.0;

      switch(risk_mode)
      {
         case RISK_MODE_PERCENT:
         {
            plan.risk_percent = risk_input_value;
            plan.risk_money   = account_funds * (plan.risk_percent / 100.0);
            calculated_lots   = plan.risk_money / loss_1_lot;
            break;
         }
         case RISK_MODE_MONEY:
         {
            plan.risk_money   = risk_input_value;
            plan.risk_percent = (account_funds > 0.0) ? (plan.risk_money / account_funds) * 100.0 : 0.0;
            calculated_lots   = plan.risk_money / loss_1_lot;
            break;
         }
         case RISK_MODE_FIXED_LOT:
         {
            calculated_lots   = risk_input_value;
            plan.risk_money   = calculated_lots * loss_1_lot;
            plan.risk_percent = (account_funds > 0.0) ? (plan.risk_money / account_funds) * 100.0 : 0.0;
            break;
         }
      }

      // Normalize total lots
      plan.total_lots = NormalizeLots(calculated_lots);
      // Recompute actual cash risk and % from normalized lots
      plan.risk_money   = NormalizeDouble(plan.total_lots * loss_1_lot, 2);
      plan.risk_percent = (account_funds > 0.0) ? NormalizeDouble((plan.risk_money / account_funds) * 100.0, 2) : 0.0;

      // 5. Multi-Target Volume Allocation
      if(plan.num_targets < 1) plan.num_targets = 1;
      if(plan.num_targets > 3) plan.num_targets = 3;

      // Normalize shares
      double share_sum = 0.0;
      for(int i = 0; i < plan.num_targets; i++)
      {
         if(plan.tp_shares[i] <= 0.0)
            plan.tp_shares[i] = (plan.num_targets == 1) ? 100.0 : (100.0 / plan.num_targets);
         share_sum += plan.tp_shares[i];
      }
      if(share_sum <= 0.0) share_sum = 100.0;

      double allocated_sum = 0.0;
      for(int i = 0; i < plan.num_targets; i++)
      {
         double raw_target_lots = plan.total_lots * (plan.tp_shares[i] / share_sum);
         double steps = MathFloor(raw_target_lots / m_vol_step + 0.0000001);
         double t_lot = NormalizeDouble(steps * m_vol_step, m_lot_digits);
         
         // Minimum lot enforcement
         if(t_lot < m_vol_min && plan.total_lots >= m_vol_min && i == 0)
            t_lot = m_vol_min;

         plan.target_lots[i] = t_lot;
         allocated_sum += t_lot;
      }

      // Distribute any remainder due to rounding to Target 1
      double remainder = NormalizeDouble(plan.total_lots - allocated_sum, m_lot_digits);
      if(MathAbs(remainder) >= m_vol_step)
      {
         plan.target_lots[0] = NormalizeDouble(plan.target_lots[0] + remainder, m_lot_digits);
         if(plan.target_lots[0] < m_vol_min)
            plan.target_lots[0] = m_vol_min;
      }

      // 6. TP Distances, Rewards & Risk/Reward Ratios
      plan.total_reward_money = 0.0;

      for(int i = 0; i < plan.num_targets; i++)
      {
         if(plan.tp_prices[i] > 0.0)
         {
            double tp_diff = MathAbs(plan.tp_prices[i] - plan.entry_price);
            plan.tp_distance_points[i] = (m_point > 0.0) ? NormalizeDouble(tp_diff / m_point, 1) : 0.0;
            plan.tp_distance_pips[i]   = (m_point > 0.0) ? NormalizeDouble(tp_diff / (m_point * 10.0), 1) : 0.0;

            double profit_1_lot = CalculateProfitPerLot(plan.direction, plan.entry_price, plan.tp_prices[i]);
            plan.reward_money[i] = NormalizeDouble(profit_1_lot * plan.target_lots[i], 2);
            plan.total_reward_money += plan.reward_money[i];

            if(sl_diff > 0.0000001)
               plan.risk_reward_ratios[i] = NormalizeDouble(tp_diff / sl_diff, 2);
            else
               plan.risk_reward_ratios[i] = 0.0;
         }
         else
         {
            plan.tp_distance_points[i] = 0.0;
            plan.tp_distance_pips[i]   = 0.0;
            plan.reward_money[i]       = 0.0;
            plan.risk_reward_ratios[i] = 0.0;
         }
      }

      // Calculate blended average R:R
      if(plan.risk_money > 0.001)
         plan.avg_rr_ratio = NormalizeDouble(plan.total_reward_money / plan.risk_money, 2);
      else
         plan.avg_rr_ratio = (plan.num_targets > 0) ? plan.risk_reward_ratios[0] : 0.0;

      return true;
   }

   //+------------------------------------------------------------------+
   //| Adjust Take Profit level to achieve a specific Risk:Reward ratio |
   //+------------------------------------------------------------------+
   double CalculateTPFromRR(ENUM_TRADE_DIR dir, double entry, double sl, double target_rr)
   {
      double sl_dist = MathAbs(entry - sl);
      double tp_dist = sl_dist * target_rr;

      if(dir == TRADE_DIR_BUY)
         return NormalizeDouble(entry + tp_dist, m_digits);
      else
         return NormalizeDouble(entry - tp_dist, m_digits);
   }

   // Getters
   string GetSymbol(void)      const { return m_symbol; }
   int    GetDigits(void)      const { return m_digits; }
   double GetPoint(void)       const { return m_point; }
   double GetTickSize(void)    const { return m_tick_size; }
   double GetMinLot(void)      const { return m_vol_min; }
   double GetMaxLot(void)      const { return m_vol_max; }
   double GetLotStep(void)     const { return m_vol_step; }
   int    GetLotDigits(void)   const { return m_lot_digits; }
};

