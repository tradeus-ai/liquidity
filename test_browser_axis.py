from playwright.sync_api import sync_playwright
import time
import subprocess
import threading

def run_server():
    subprocess.run(["./.venv/bin/python", "app.py"])

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(3) # Wait for server to start

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://127.0.0.1:8080/?symbol=AXISBANK')
    page.wait_for_selector('canvas', timeout=15000)
    time.sleep(5)
    page.screenshot(path='/home/arun-sush/.gemini/antigravity-ide/brain/000be0c0-b7c0-4924-8e52-572cd96e324d/screenshot_axisbank2.png')
    browser.close()
