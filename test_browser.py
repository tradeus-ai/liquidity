from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://127.0.0.1:8080/?symbol=ABB')
    page.wait_for_selector('canvas') # Wait for chart
    time.sleep(5) # Wait for rendering
    page.screenshot(path='/home/arun-sush/.gemini/antigravity-ide/brain/000be0c0-b7c0-4924-8e52-572cd96e324d/screenshot.png')
    browser.close()
