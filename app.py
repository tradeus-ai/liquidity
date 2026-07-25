import http.server
import socketserver
import json
import urllib.parse
import os
import sys

from symbol_loader import get_symbol_list
from web_dashboard import render_dashboard

PORT = 8080
FEEDBACK_FILE = "chart_feedback.json"

class LiquidityDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        # 1. API: Get Symbols List
        if path == '/api/symbols':
            symbols = get_symbol_list()
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
            chart_data = get_chart_data(symbol, timeframe)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(chart_data).encode('utf-8'))
            return

        # 2. Serve Dynamic Interactive Dashboard with Symbol & Timeframe controls
        elif path in ['/', '/index.html', '/dashboard.html']:
            symbol = query.get('symbol', ['AMBUJACEM'])[0]
            timeframe = query.get('timeframe', ['1d'])[0]

            print(f"📊 Rendering dashboard for symbol='{symbol}', timeframe='{timeframe}'...")
            html_content = render_dashboard(symbol, timeframe)

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
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), LiquidityDashboardHandler) as httpd:
        print(f"=" * 80)
        print(f"🚀 Liquidity Dashboard running at http://127.0.0.1:{PORT}")
        print(f"Features: Multi-Symbol Dropdown (215+ symbols), Timeframes (1D, 1H, 15m, 5m), White Candles, Orange Pullback, Pink Inside Boxes")
        print(f"=" * 80)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
