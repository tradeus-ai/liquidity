import http.server
import socketserver
import json
import urllib.parse
import os
import sys

from symbol_loader import get_symbol_list
from web_dashboard import render_dashboard

PORT = int(os.environ.get("PORT", 8080))
FEEDBACK_FILE = "chart_feedback.json"

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

class LiquidityDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        # 1. API: Get Symbols List
        if path == '/api/symbols':
            market_type = query.get('type', ['futures'])[0]
            symbols = get_symbol_list(market_type)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(symbols).encode('utf-8'))
            return

        # 1b. API: Get Chart Structure Data
        elif path == '/api/data':
            from structure_service import get_chart_data
            symbol = query.get('symbol', ['AMBUJACEM'])[0]
            timeframe = query.get('timeframe', ['1d'])[0]
            market_type = query.get('type', ['futures'])[0]
            chart_data = get_chart_data(symbol, timeframe, market_type)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(chart_data).encode('utf-8'))
            return

        # 1c. API: Get Screener Data
        elif path == '/api/screener':
            from screener_service import get_screener_data
            force_refresh = query.get('refresh', ['false'])[0].lower() == 'true'
            screener_data = get_screener_data(force_refresh=force_refresh)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(screener_data).encode('utf-8'))
            return

        # 2. Serve Dynamic Interactive Dashboard with Symbol & Timeframe controls
        elif path in ['/', '/index.html', '/dashboard.html']:
            requested_type = query.get('type', [None])[0]
            requested_symbol = query.get('symbol', [None])[0]
            
            if requested_symbol and not requested_type:
                clean_sym = requested_symbol.upper().replace('1!', '').strip()
                if clean_sym in {'AUDUSD', 'EURUSD', 'USDJPY', 'GBPUSD', 'USDCAD', 'USDCHF', 'NZDUSD'}:
                    market_type = 'forex'
                elif clean_sym in {'XAUUSD', 'XAGUSD'}:
                    market_type = 'metals'
                else:
                    market_type = 'futures'
            else:
                market_type = requested_type or 'futures'
                
            default_symbols = get_symbol_list(market_type)
            default_symbol = default_symbols[0] if default_symbols else 'AMBUJACEM'
            
            symbol = requested_symbol or default_symbol
            timeframe = query.get('timeframe', ['1d'])[0]

            print(f"📊 Rendering dashboard for symbol='{symbol}', timeframe='{timeframe}', market_type='{market_type}'...")
            html_content = render_dashboard(symbol, timeframe, market_type)

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            return

        # 3. Serve Screener UI
        elif path in ['/screener', '/screener.html']:
            with open("screener.html", "r", encoding="utf-8") as f:
                html_content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            return

        # Fallback to static file handler
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/feedback':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))

                feedbacks = []
                if os.path.exists(FEEDBACK_FILE):
                    with open(FEEDBACK_FILE, 'r') as f:
                        try:
                            feedbacks = json.load(f)
                        except json.JSONDecodeError:
                            feedbacks = []

                feedbacks.append(data)

                with open(FEEDBACK_FILE, 'w') as f:
                    json.dump(feedbacks, f, indent=4)

                print(f"✅ Feedback received and saved: {data}")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except Exception as e:
                print(f"❌ Error processing feedback: {e}")
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "error"}')
        else:
            self.send_error(404)

if __name__ == "__main__":
    from apscheduler.schedulers.background import BackgroundScheduler
    from screener_service import get_screener_data

    # Schedule daily screener cache recalculation in the background
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: get_screener_data(force_refresh=True), trigger="cron", hour=0, minute=0)
    scheduler.start()
    print("⏰ Background scheduler started for daily screener cache updates.")

    with ThreadedTCPServer(("", PORT), LiquidityDashboardHandler) as httpd:
        print(f"=" * 80)
        print(f"🚀 Liquidity Dashboard running at http://127.0.0.1:{PORT}")
        print(f"Features: Multi-Symbol Dropdown (215+ symbols), Timeframes (1D, 4H, 1H, 15m, 5m), White Candles, Orange Pullback, Pink Inside Boxes")
        print(f"=" * 80)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            scheduler.shutdown()
