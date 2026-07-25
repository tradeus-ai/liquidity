import http.server
import socketserver
import json
import logging
import os

PORT = 8080
FEEDBACK_FILE = "chart_feedback.json"

class FeedbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()
        
    def do_POST(self):
        if self.path == '/feedback':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Append to feedback file
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
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except Exception as e:
                print(f"❌ Error processing feedback: {e}")
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "error"}')
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), FeedbackHandler) as httpd:
        print(f"🚀 Feedback server running at http://127.0.0.1:{PORT}")
        print(f"Waiting for feedback from interactive charts...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down feedback server.")
