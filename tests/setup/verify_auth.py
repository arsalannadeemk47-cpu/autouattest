import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

AUTH_STATE = "/workspaces/autouattest/tests/setup/.auth/user.json"
TARGET_URL = "https://lacps--uat.sandbox.my.site.com/s/"

# Selectors that only appear when logged in
AUTHENTICATED_INDICATORS = [
    'text=My Open Tasks'
]

# Selectors that indicate we are NOT logged in
UNAUTHENTICATED_INDICATORS = [
    'button:has-text("Log In")'
]

async def verify_cookies():
    print("🔍 Verifying cookie session...\n")

    # Check file exists and has content
    if not os.path.exists(AUTH_STATE):
        print("❌ user.json not found at:", AUTH_STATE)
        print("   Run build_auth.py first to create it.")
        return False

    with open(AUTH_STATE) as f:
        state = json.load(f)

    cookies = state.get("cookies", [])
    if not cookies:
        print("❌ user.json exists but contains no cookies.")
        return False

    # Check for critical Salesforce session cookie
    sid_cookie = next((c for c in cookies if c["name"] == "sid"), None)
    if not sid_cookie:
        print("❌ No 'sid' session cookie found — authentication will fail.")
        return False

    print(f"✅ Found {len(cookies)} cookies")
    print(f"✅ Salesforce sid cookie present")

    # Now verify the session actually works in a real browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=AUTH_STATE)
        page = await context.new_page()

        print(f"\n🌐 Loading {TARGET_URL}...")
        await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)

        current_url = page.url
        print(f"📍 Current URL: {current_url}")

        # Check for unauthenticated indicators first
        # Check for unauthenticated indicators first
        for selector in UNAUTHENTICATED_INDICATORS:
            try:
                el = page.locator(selector).first
                visible = await el.is_visible(timeout=2000)
            except Exception:
                visible = False
            if visible:
                print(f"\n❌ Session expired or invalid.")
                print(f"   Found unauthenticated element: {selector}")
                print(f"\n   Please refresh your cookies:")
                print(f"   1. Log in to the site in Chrome")
                print(f"   2. Copy cookies from DevTools Network tab")
                print(f"   3. Update COOKIE_STRING in build_auth.py")
                print(f"   4. Run: python tests/setup/build_auth.py")
                await browser.close()
                return False

        # Check for authenticated indicators
            for selector in AUTHENTICATED_INDICATORS:
                try:
                    el = page.locator(selector).first
                    visible = await el.is_visible(timeout=2000)
                except Exception:
                    visible = False
                if visible:
                    print(f"\n✅ Session is valid — authenticated element found")
                    print(f"   Selector: {selector}")
                    await browser.close()
                    return True

            # If neither found, check URL for login redirect
            if 'login' in current_url.lower():
                print(f"\n❌ Redirected to login page — session has expired")
                print(f"   Please refresh your cookies and try again")
                await browser.close()
                return False

            # Take a screenshot for manual inspection if uncertain
            screenshot_path = "/workspaces/autouattest/tests/setup/auth_check.png"
            await page.screenshot(path=screenshot_path)
            print(f"\n⚠️  Could not confirm authentication status automatically")
            print(f"   Screenshot saved to: {screenshot_path}")
            print(f"   Check it manually to confirm login state")

            await browser.close()
            return None

        # Check for authenticated indicators
        for selector in AUTHENTICATED_INDICATORS:
            el = page.locator(selector).first
            if await el.is_visible(timeout=2000).catch(lambda _: False):
                print(f"\n✅ Session is valid — authenticated element found")
                print(f"   Selector: {selector}")
                await browser.close()
                return True

        # If neither found, check URL for login redirect
        if 'login' in current_url.lower():
            print(f"\n❌ Redirected to login page — session has expired")
            print(f"   Please refresh your cookies and try again")
            await browser.close()
            return False

        # Take a screenshot for manual inspection if uncertain
        screenshot_path = "/workspaces/autouattest/tests/setup/auth_check.png"
        await page.screenshot(path=screenshot_path)
        print(f"\n⚠️  Could not confirm authentication status automatically")
        print(f"   Screenshot saved to: {screenshot_path}")
        print(f"   Check it manually to confirm login state")

        await browser.close()
        return None  # uncertain

if __name__ == "__main__":
    result = asyncio.run(verify_cookies())
    if result is True:
        print("\n🟢 Ready to run authenticated tests and exploration")
        sys.exit(0)
    elif result is False:
        print("\n🔴 Fix authentication before proceeding")
        sys.exit(1)
    else:
        print("\n🟡 Authentication status uncertain — check screenshot")
        sys.exit(2)