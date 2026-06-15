import asyncio
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from browser_use import Agent
from browser_use.llm import ChatAnthropic
from playwright.async_api import async_playwright

load_dotenv()

TARGET_URL = "https://lacps--uat.sandbox.my.site.com/s/"
AUTH_STATE = "/workspaces/autouattest/tests/setup/.auth/user.json"

NEW_ADDRESS = {
    "street": "350 S Bixel St",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90017"
}


async def verify_authenticated_state(page) -> bool:
    """
    Check if the current page state is authenticated.
    Returns False if login page detected, True if authenticated.
    """
    current_url = page.url

    # Check for login redirect
    if 'login' in current_url.lower():
        print("❌ Agent landed on login page — session expired")
        return False

    # Check for Log In button (unauthenticated state)
    login_btn = page.locator('button[title="Log In"]').first
    if await login_btn.is_visible(timeout=3000):
        print("❌ Login button found — not authenticated")
        return False

    print("✅ Agent confirmed authenticated state")
    return True


async def capture_profile_snapshots():
    """
    Navigate the profile flow directly with Playwright and capture
    HTML snapshots at each key stage for use as selector context.
    """
    snapshots = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=AUTH_STATE)
        page = await context.new_page()

        try:
            # Snapshot 1: Homepage authenticated state
            await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            snapshots['homepage_authenticated'] = await page.content()
            print("📸 Captured: homepage authenticated state")

           # Find and click the profile icon in top right
            profile_icon = page.locator(
                'button[aria-label*="User Profile"]'
            ).first
            await profile_icon.click()
            await page.wait_for_timeout(1500)
            snapshots['profile_menu_open'] = await page.content()
            print("📸 Captured: profile menu open")

            # Click User Settings - from HTML the menu item is "User Profile" not "User Settings"
            await page.get_by_role(
                'menuitem', name='User Profile'
            ).click()
            await page.wait_for_load_state('domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)
            snapshots['profile_page'] = await page.content()
            snapshots['profile_url'] = page.url
            print(f"📸 Captured: profile page at {page.url}")

            # Click User Settings
            await page.get_by_role(
                'link',
                name=re.compile(r'user settings|settings|my profile', re.I)
            ).first.click()
            await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            snapshots['profile_page'] = await page.content()
            snapshots['profile_url'] = page.url()
            print(f"📸 Captured: profile page at {page.url()}")

            # Check visibility of contact fields
            phone_el = page.get_by_label(re.compile(r'phone', re.I)).first
            email_el = page.get_by_label(re.compile(r'email', re.I)).first
            address_el = page.get_by_label(
                re.compile(r'address|street', re.I)
            ).first

            snapshots['contact_fields'] = {
                'phone_visible': await phone_el.is_visible(timeout=3000),
                'email_visible': await email_el.is_visible(timeout=3000),
                'address_visible': await address_el.is_visible(timeout=3000),
            }

            # Click edit button
            edit_btn = page.get_by_role(
                'button', name=re.compile(r'^edit$', re.I)
            ).or_(
                page.get_by_role('link', name=re.compile(r'^edit$', re.I))
            ).first

            if await edit_btn.is_visible(timeout=3000):
                await edit_btn.click()
                await page.wait_for_timeout(2000)
                snapshots['profile_edit_mode'] = await page.content()
                print("📸 Captured: profile edit mode")

                # Change address
                street_field = page.get_by_label(
                    re.compile(r'street|address line 1', re.I)
                ).first
                if await street_field.is_visible(timeout=3000):
                    await street_field.clear()
                    await street_field.fill(NEW_ADDRESS['street'])
                    snapshots['address_changed'] = NEW_ADDRESS
                    print(f"✏️  Changed street to: {NEW_ADDRESS['street']}")

            # Snapshot role/user type section
            await page.wait_for_timeout(1000)
            role_section = page.locator(
                '[class*="role"], [class*="user-type"], '
                'text=/user type|user role|roles/i'
            ).first

            if await role_section.is_visible(timeout=3000):
                snapshots['role_section'] = await role_section.inner_html()
                print("📸 Captured: role section")

            # Check move selection buttons
            move_to_chosen = page.get_by_role(
                'button',
                name=re.compile(r'move.*chosen|add.*chosen|move.*selected', re.I)
            ).first
            move_to_available = page.get_by_role(
                'button',
                name=re.compile(r'move.*available|remove.*chosen', re.I)
            ).first

            snapshots['role_buttons'] = {
                'move_to_chosen_visible': await move_to_chosen.is_visible(
                    timeout=3000
                ),
                'move_to_available_visible': await move_to_available.is_visible(
                    timeout=3000
                ),
            }

            # Final full page snapshot
            snapshots['profile_page_final'] = await page.content()
            print("📸 Captured: final profile page state")

        except Exception as e:
            snapshots['capture_error'] = str(e)
            print(f"⚠️  Snapshot error: {e}")
            snapshots['error_page_state'] = await page.content()

        await browser.close()

    return snapshots


async def run_profile_explorer():
    print("🤖 Profile explorer agent starting...\n")

    # Pre-flight auth check before launching agent
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=AUTH_STATE)
        page = await context.new_page()
        await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)

        is_authenticated = await verify_authenticated_state(page)
        await browser.close()

    if not is_authenticated:
        print("\n🔴 Aborting exploration — not authenticated")
        print("   Refresh cookies and try again:")
        print("   1. Log in to the site in Chrome")
        print("   2. Copy cookies from DevTools Network tab")
        print("   3. Update COOKIE_STRING in build_auth.py")
        print("   4. Run: python tests/setup/build_auth.py")
        return None

    print("🟢 Authentication confirmed — launching agent\n")

    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    agent = Agent(
        task=f"""
        You are a test automation agent exploring a user profile
        settings page on an authenticated website.

        Target site: {TARGET_URL}
        You are already authenticated via saved session cookies.

        Instructions:
        1. Navigate to the homepage
        2.  Find the profile/account icon in the TOP RIGHT corner
           of the screen. It is a button with aria-label starting
           with "User Profile". Click it to open the dropdown menu.
        3. In the dropdown menu, click "User Profile" (not User Settings)
        4. On the profile/settings page, carefully record:
           - The exact URL of the settings page
           - The exact label text of the phone number field
           - The exact label text of the email address field
           - The exact label text of the address fields
             (street, city, state, zip — record each separately)
           - The current values in these fields if visible
        5. Find the Edit button and click it
        6. Record:
           - What changed on the page after clicking Edit
           - Which fields became editable
           - The exact label text of each editable field
        7. Find the User Type or User Role section and record:
           - The exact heading text of this section
           - The exact button text of the "move to chosen" button
           - The exact button text of the "move to available" button
           - What options are in the "available" list
           - What options are in the "chosen" list
        8. Record ALL button text, field labels, and section
           headings EXACTLY as they appear — do not paraphrase

        Return a detailed JSON log of all findings.
        """,
        llm=llm,
        use_vision=False,
        max_failures=3,
        max_actions_per_step=3,
        max_history_items=10,
        calculate_cost=True,
    )

    agent_result = await agent.run(max_steps=30)

    # Capture HTML snapshots
    print("\n📸 Capturing HTML snapshots...\n")
    try:
        snapshots = await capture_profile_snapshots()
        print(f"✅ Captured {len(snapshots)} snapshots")
    except Exception as e:
        print(f"⚠️  Snapshot capture failed: {e}")
        snapshots = {}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = (
        f"/workspaces/autouattest/agents/logs/"
        f"profile_discovery_{timestamp}.json"
    )
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    discovery = {
        "agent": "profile_explorer",
        "target": TARGET_URL,
        "timestamp": timestamp,
        "new_address_used": NEW_ADDRESS,
        "agent_findings": str(agent_result),
        "html_snapshots": snapshots
    }

    with open(log_path, "w") as f:
        json.dump(discovery, f, indent=2)

    # Save persistent context for future agents
    context_path = (
        "/workspaces/autouattest/agents/context/profile_context.json"
    )
    os.makedirs(os.path.dirname(context_path), exist_ok=True)

    with open(context_path, "w") as f:
        json.dump({
            "description": "User profile page exploration context",
            "last_updated": timestamp,
            "profile_url": snapshots.get("profile_url", "unknown"),
            "agent_findings": str(agent_result),
            "contact_fields_found": snapshots.get("contact_fields", {}),
            "role_buttons_found": snapshots.get("role_buttons", {}),
            "new_address_tested": NEW_ADDRESS,
            "html_snapshots": {
                k: v for k, v in snapshots.items()
                if k in [
                    'profile_page',
                    'profile_edit_mode',
                    'profile_page_final'
                ]
            }
        }, f, indent=2)

    print(f"\n✅ Discovery log saved to {log_path}")
    print(f"✅ Context saved to {context_path}")
    print("\n--- Agent Findings ---")
    print(agent_result)

    return log_path

if __name__ == "__main__":
    asyncio.run(run_profile_explorer())