import sqlite3
from datetime import datetime
import pandas as pd

class TradeManager:
    def __init__(self, db_path='trades.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS trades
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      symbol TEXT,
                      direction TEXT,
                      entry_price REAL,
                      sl_price REAL,
                      t1_price REAL,
                      t2_price REAL,
                      status TEXT DEFAULT 'OPEN',
                      entry_time TEXT,
                      exit_time TEXT,
                      exit_price REAL,
                      pnl REAL)''')
        conn.commit()
        conn.close()

    def has_active_trade(self, symbol):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM trades WHERE symbol = ? AND status IN ('OPEN', 'T1_HIT')", (symbol,))
        row = c.fetchone()
        conn.close()
        return row is not None

    def open_trade(self, symbol, direction, entry_price, sl_price, t1_price, t2_price, alert_mgr):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("""INSERT INTO trades 
                     (symbol, direction, entry_price, sl_price, t1_price, t2_price, status, entry_time)
                     VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?)""",
                  (symbol, direction, entry_price, sl_price, t1_price, t2_price, now))
        trade_id = c.lastrowid
        conn.commit()
        conn.close()
        
        msg = f"🟢 NEW TRADE OPENED: {direction} {symbol}\nEntry: {entry_price}\nSL: {sl_price}\nT1: {t1_price}\nT2: {t2_price}"
        alert_mgr.queue_alert(symbol, msg)

    def check_and_update_trades(self, symbol, current_high, current_low, current_close, alert_mgr):
        """Evaluate open trades against the current candle's high/low."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, direction, entry_price, sl_price, t1_price, t2_price, status FROM trades WHERE symbol = ? AND status IN ('OPEN', 'T1_HIT')", (symbol,))
        trades = c.fetchall()
        
        for trade in trades:
            t_id, direction, entry_price, sl_price, t1_price, t2_price, status = trade
            now = datetime.utcnow().isoformat()
            
            new_status = status
            exit_price = None
            msg = None
            
            if direction == 'BUY':
                # Check SL first
                if current_low <= sl_price:
                    if status == 'T1_HIT':
                        new_status = 'CLOSED_COST'
                        exit_price = sl_price
                        msg = f"⚪ COST TO COST SL HIT: {symbol} Buy at {entry_price}"
                    else:
                        new_status = 'CLOSED_LOSS'
                        exit_price = sl_price
                        msg = f"🔴 SL HIT - LOST TRADE: {symbol} Buy. Hit {sl_price}"
                
                # Check T2
                elif status == 'T1_HIT' and current_high >= t2_price:
                    new_status = 'CLOSED_WIN'
                    exit_price = t2_price
                    msg = f"🎯 TARGET 2 REACHED - EXIT POSITION: {symbol} Buy at {t2_price}"
                    
                # Check T1
                elif status == 'OPEN' and current_high >= t1_price:
                    new_status = 'T1_HIT'
                    # Update SL to cost
                    c.execute("UPDATE trades SET status = ?, sl_price = ? WHERE id = ?", (new_status, entry_price, t_id))
                    msg = f"✅ TARGET 1 REACHED: {symbol} Buy. SL updated to Entry ({entry_price})"
                    
            elif direction == 'SELL':
                # Check SL first
                if current_high >= sl_price:
                    if status == 'T1_HIT':
                        new_status = 'CLOSED_COST'
                        exit_price = sl_price
                        msg = f"⚪ COST TO COST SL HIT: {symbol} Sell at {entry_price}"
                    else:
                        new_status = 'CLOSED_LOSS'
                        exit_price = sl_price
                        msg = f"🔴 SL HIT - LOST TRADE: {symbol} Sell. Hit {sl_price}"
                
                # Check T2
                elif status == 'T1_HIT' and current_low <= t2_price:
                    new_status = 'CLOSED_WIN'
                    exit_price = t2_price
                    msg = f"🎯 TARGET 2 REACHED - EXIT POSITION: {symbol} Sell at {t2_price}"
                    
                # Check T1
                elif status == 'OPEN' and current_low <= t1_price:
                    new_status = 'T1_HIT'
                    # Update SL to cost
                    c.execute("UPDATE trades SET status = ?, sl_price = ? WHERE id = ?", (new_status, entry_price, t_id))
                    msg = f"✅ TARGET 1 REACHED: {symbol} Sell. SL updated to Entry ({entry_price})"

            if msg:
                alert_mgr.queue_alert(symbol, msg)
                
            if new_status in ['CLOSED_WIN', 'CLOSED_LOSS', 'CLOSED_COST']:
                pnl = exit_price - entry_price if direction == 'BUY' else entry_price - exit_price
                c.execute("UPDATE trades SET status = ?, exit_time = ?, exit_price = ?, pnl = ? WHERE id = ?", 
                          (new_status, now, exit_price, pnl, t_id))
                          
        conn.commit()
        conn.close()

    def get_stats_summary(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades WHERE status LIKE 'CLOSED%'", conn)
        conn.close()
        
        if df.empty:
            return "No closed trades yet."
            
        wins = len(df[df['status'] == 'CLOSED_WIN'])
        losses = len(df[df['status'] == 'CLOSED_LOSS'])
        cost = len(df[df['status'] == 'CLOSED_COST'])
        total = len(df)
        win_rate = (wins / total) * 100 if total > 0 else 0
        
        return f"📊 Trade Stats:\nTotal: {total}\nWins: {wins}\nLosses: {losses}\nCost-to-Cost: {cost}\nWin Rate: {win_rate:.2f}%"
