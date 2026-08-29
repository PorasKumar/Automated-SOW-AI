import time
from playwright.sync_api import sync_playwright

APP_URL = "https://automated-sow-engine.streamlit.app/"

def wake_up_app():
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Navigating to {APP_URL}...")
        page.goto(APP_URL, timeout=60000)

        # Allow initial DOM rendering
        page.wait_for_timeout(5000)

        # Look for Streamlit's wake button
        wake_button = page.get_by_role("button", name="Yes, get this app back up!")

        if wake_button.is_visible():
            print("⚠️ App is asleep. Clicking 'Yes, get this app back up!' button...")
            wake_button.click()
            print("⏳ Clicked wake button. Waiting for app to spin up...")
            
            # Wait up to 30 seconds for app to fully boot
            page.wait_for_timeout(30000)
            print("✅ App wakeup sequence completed!")
        else:
            print("✨ App is already awake and active!")

        browser.close()

if __name__ == "__main__":
    wake_up_app()