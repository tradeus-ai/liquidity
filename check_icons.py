import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("pageerror", lambda err: errors.append(err.message))
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}") if msg.type == 'error' else None)
        
        await page.goto("http://localhost:8081/?symbol=ADANIGREEN")
        await page.wait_for_timeout(2000)
        
        print("JS Errors on page:", errors)
        
        html = await page.evaluate("() => document.querySelector('.legend').outerHTML")
        print("Legend text content:", await page.evaluate("() => document.querySelector('.legend').innerText"))
        
        await browser.close()

asyncio.run(main())
