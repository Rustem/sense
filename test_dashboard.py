"""Quick Playwright script to screenshot dashboard."""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto("http://localhost:8000")
    page.wait_for_timeout(2000)  # Wait for charts to render
    page.screenshot(path="dashboard_screenshot.png", full_page=True)
    browser.close()
    print("Screenshot saved to dashboard_screenshot.png")
