import sqlite3
import asyncio
from telegram import Bot
from telegram.error import TelegramError

class AlertManager:
    def __init__(self, db_path='alerts.db', telegram_token=None, chat_id=None):
        self.db_path = db_path
        self.token = telegram_token
        self.chat_id = chat_id
        if self.token:
            self.bot = Bot(token=self.token)
        else:
            self.bot = None
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS pending_alerts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      symbol TEXT,
                      message TEXT,
                      retries INTEGER DEFAULT 0,
                      status TEXT DEFAULT 'pending')''')
        conn.commit()
        conn.close()

    def queue_alert(self, symbol, message):
        """Add a new alert to the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO pending_alerts (symbol, message) VALUES (?, ?)", (symbol, message))
        conn.commit()
        conn.close()
        print(f"Alert queued for {symbol}: {message}")

    async def worker_loop(self):
        """Continuously check DB for pending alerts and try to send them via Telegram with backoff."""
        while True:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT id, symbol, message, retries FROM pending_alerts WHERE status = 'pending' AND retries < 5")
                alerts = c.fetchall()
                
                for alert_id, symbol, message, retries in alerts:
                    full_message = f"🚨 Alert for {symbol} 🚨\n{message}"
                    success = False
                    
                    if self.bot and self.chat_id:
                        try:
                            await self.bot.send_message(chat_id=self.chat_id, text=full_message)
                            success = True
                        except TelegramError as e:
                            print(f"Telegram error sending alert {alert_id}: {e}")
                    else:
                        print(f"STUB (no token): Would send telegram: {full_message}")
                        success = True
                        
                    if success:
                        c.execute("UPDATE pending_alerts SET status = 'sent' WHERE id = ?", (alert_id,))
                    else:
                        c.execute("UPDATE pending_alerts SET retries = retries + 1 WHERE id = ?", (alert_id,))
                        
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error in alert worker: {e}")
            
            await asyncio.sleep(10) # check every 10 seconds
