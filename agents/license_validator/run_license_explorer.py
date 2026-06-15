import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from browser_use import Agent
from browser_use.llm import ChatAnthropic
from playwright.async_api import async_playwright
from license_data import TESTABLE_LICENSES

load_dotenv()

TARGET_URL = "https://lacps--uat.sandbox.my.site.com/s/"
AUTH_STATE = "/workspaces/autouattest/tests/setup/.auth/user.json"
SEARCH_ADDRESS = "3761 S D"
SELECT_ADDRESS = "3761 S Dunn Dr"


async def verify_authenticated_state(page) -> bool:
    current_url = page.url
    if 'login' in current_url.lower():
        print("❌ Landed on login page — session expired")
        return False
    try:
        profile_btn = page.locator(
            'button[aria-label*="User Profile"]'
        ).first
        visible = await profile_btn.is_visible(timeout=5000)
        if visible:
            print("✅ Authenticated state confirmed")
            return True
    except Exception:
        pass
    try:
        login_btn = page.locator('button[title="Log In"]').first
        visible = await login_btn.is_visible(timeout=3000)
        if visible:
            print("❌ Login button found — not authenticated")
            return False
    except Exception:
        pass
    print("⚠️  Auth status uncertain — proceeding")
    return True


async def capture_workflow_snapshots():
    """
    Navigate the permit application workflow with Playwright directly
    to capture HTML snapshots at each key stage for selector context.
    Only navigates through the workflow once to capture the structure —
    does not test each license (that is done in the generated tests).
    """
    snapshots = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=AUTH_STATE)
        page = await context.new_page()

        try:
            # Step 1: Homepage
            await page.goto(TARGET_URL)
            await page.wait_for_load_state(
                'domcontentloaded', timeout=30000
            )
            await page.wait_for_timeout(3000)
            snapshots['homepage'] = await page.content()
            print("📸 Captured: homepage")

            # Step 2: Permits menu → New Permit Application
            await page.get_by_role(
                'button', name='Permits', exact=False
            ).click()
            await page.wait_for_timeout(1500)
            snapshots['permits_menu_open'] = await page.content()
            print("📸 Captured: permits menu open")

            await page.get_by_role(
                'link', name='New Permit Application'
            ).click()
            await page.wait_for_load_state(
                'domcontentloaded', timeout=30000
            )
            await page.wait_for_timeout(3000)
            snapshots['new_permit_page'] = await page.content()
            snapshots['new_permit_url'] = page.url
            print(f"📸 Captured: new permit page at {page.url}")

            # Step 3: Start New Application
            start_btn = page.get_by_role(
                'button', name='Start New Application'
            ).or_(page.get_by_text('Start New Application')).first
            await start_btn.click()
            await page.wait_for_timeout(3000)
            snapshots['after_start'] = await page.content()
            print("📸 Captured: after start new application")

           # Step 4: Select Pre-Defined Scope
            predefined = page.locator(
                'input[type="radio"][value="Pre-Defined Scope"]'
            )
            if await predefined.is_visible(timeout=5000):
                await predefined.click()
                await page.wait_for_timeout(2000)
                snapshots['predefined_scope_selected'] = \
                    await page.content()
                print("📸 Captured: pre-defined scope selected")

            # Step 5: Address search
            addr_input = page.get_by_role(
                'textbox', name='Address'
            ).or_(
                page.get_by_placeholder(
                    'Search address', exact=False
                )
            ).first
            await addr_input.fill(SEARCH_ADDRESS)
            await page.wait_for_timeout(2000)
            snapshots['address_search_results'] = await page.content()
            print("📸 Captured: address search results")

            # Select the address from dropdown
            addr_option = page.get_by_text(
                SELECT_ADDRESS, exact=False
            ).first
            if await addr_option.is_visible(timeout=5000):
                await addr_option.click()
                await page.wait_for_timeout(2000)

            # Click Next
            next_btn = page.get_by_role(
                'button', name='Next'
            ).last
            await next_btn.click()
            await page.wait_for_timeout(3000)
            snapshots['after_address_next'] = await page.content()
            print("📸 Captured: after address next")

            # Step 6: Click Next on the following screen
            next_btn2 = page.get_by_role('button', name='Next').last
            await next_btn2.click()
            await page.wait_for_timeout(3000)
            snapshots['applicant_details_page'] = await page.content()
            snapshots['applicant_details_url'] = page.url
            print(
                f"📸 Captured: applicant details page at {page.url}"
            )

            # Step 7: Capture the Applicant Role dropdown options
            role_dropdown = page.get_by_label(
                'Applicant Role', exact=False
            ).or_(
                page.get_by_role(
                    'combobox', name='Applicant Role'
                )
            ).first
            if await role_dropdown.is_visible(timeout=5000):
                snapshots['applicant_role_dropdown_html'] = \
                    await role_dropdown.inner_html()
                print("📸 Captured: applicant role dropdown")

            # Select Contractor
            await role_dropdown.select_option('Contractor')
            await page.wait_for_timeout(2000)
            snapshots['after_contractor_selected'] = \
                await page.content()
            print("📸 Captured: after contractor selected")

            # Step 8: Select Existing License on my account
            existing_license = page.get_by_text(
                'Existing License on my account', exact=False
            ).or_(
                page.get_by_label(
                    'Existing License on my account', exact=False
                )
            ).first
            if await existing_license.is_visible(timeout=5000):
                await existing_license.click()
                await page.wait_for_timeout(2000)
                snapshots['existing_license_selected'] = \
                    await page.content()
                print("📸 Captured: existing license option selected")

            # Step 9: Capture license number and license type fields
            license_num_field = page.get_by_label(
                'License Number', exact=False
            ).first
            license_type_field = page.get_by_label(
                'License Type', exact=False
            ).or_(
                page.get_by_label('Existing License Type', exact=False)
            ).first

            snapshots['license_fields'] = {
                'license_number_visible': await license_num_field.is_visible(
                    timeout=3000
                ),
                'license_type_visible': await license_type_field.is_visible(
                    timeout=3000
                ),
            }

            # Use first testable license to capture the template page
            first_license = TESTABLE_LICENSES[0]
            await license_num_field.fill(first_license['license_number'])
            await page.wait_for_timeout(1000)

            # Select license type
            await license_type_field.select_option(
                first_license['license_code']
            )
            await page.wait_for_timeout(1000)

            # Click Load From CSLB
            cslb_btn = page.get_by_role(
                'button', name='Load From CSLB', exact=False
            ).or_(
                page.get_by_text('Load From CSLB', exact=False)
            ).first
            if await cslb_btn.is_visible(timeout=5000):
                await cslb_btn.click()
                print("⏳ Waiting for 'Successfully loaded!'...")
                await page.get_by_text(
                    'Successfully loaded!', exact=False
                ).wait_for(timeout=30000)
                await page.wait_for_timeout(1000)
                snapshots['after_cslb_load'] = await page.content()
                print("📸 Captured: after CSLB load")

            # Click Next
            next_btn3 = page.get_by_role('button', name='Next').last
            await next_btn3.click()
            await page.wait_for_timeout(3000)
            snapshots['application_template_page'] = \
                await page.content()
            snapshots['application_template_url'] = page.url
            print(
                f"📸 Captured: application template page at {page.url}"
            )

            # Capture template options
            template_options = await page.locator(
                '[class*="template"], [class*="permit-type"], '
                '[role="option"], [role="radio"]'
            ).all_text_contents()
            snapshots['template_options_found'] = template_options
            print(f"📸 Template options found: {template_options}")

        except Exception as e:
            snapshots['capture_error'] = str(e)
            print(f"⚠️  Snapshot error: {e}")
            snapshots['error_page_state'] = await page.content()

        await browser.close()

    return snapshots


async def run_license_explorer():
    print("🤖 License validator explorer starting...\n")

    # Pre-flight auth check
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=AUTH_STATE)
        page = await context.new_page()
        await page.goto(TARGET_URL)
        await page.wait_for_load_state(
            'domcontentloaded', timeout=30000
        )
        await page.wait_for_timeout(3000)
        is_authenticated = await verify_authenticated_state(page)
        await browser.close()

    if not is_authenticated:
        print("\n🔴 Aborting — not authenticated")
        print("   Refresh cookies and try again")
        return None

    print("🟢 Authentication confirmed — launching agent\n")

    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    agent = Agent(
        task=f"""
        You are a test automation agent exploring a permit application
        workflow. You are already authenticated.

        Target site: {TARGET_URL}
        Search address to use: "{SEARCH_ADDRESS}"
        Address to select: "{SELECT_ADDRESS}"

        Follow these steps EXACTLY and record findings at each step:

        1. Navigate to the homepage
        2. Find the "Permits" navigation menu and click it
        3. Click "New Permit Application"
        4. Click "Start New Application"
        5. Select "Pre-Defined Scope"
        6. In the address search field, type "{SEARCH_ADDRESS}"
        7. From the dropdown, select "{SELECT_ADDRESS}"
        8. Click Next
        9. Click Next again on the following screen
        10. You are now on the Applicant Details screen. Record:
            - The exact label of the Applicant Role dropdown
            - All available options in that dropdown
            - The exact label and options for license-related fields
            - The exact text of the "Load From CSLB" button
            - The exact text of any success message after loading
        11. Select "Contractor" from Applicant Role
        12. Select "Existing License on my account"
        13. Enter license number: {TESTABLE_LICENSES[0]['license_number']}
        14. Select license type: {TESTABLE_LICENSES[0]['license_code']}
        15. Click "Load From CSLB" and wait for success message
        16. Click Next
        17. You are now on the Application Template screen. Record:
            - The exact URL
            - The exact text of ALL available permit/template options
            - How the options are displayed (radio buttons, cards, list)
            - The exact selector/element type for each option
        18. Return a detailed JSON log of all findings including
            exact selectors, URLs, button text, and field labels.

        Do NOT assume anything. Record exact text as it appears.
        """,
        llm=llm,
        use_vision=False,
        max_failures=3,
        max_actions_per_step=3,
        max_history_items=10,
        calculate_cost=True,
    )

    print("🤖 Agent exploring license validation workflow...\n")
    agent_result = await agent.run(max_steps=40)

    # Capture HTML snapshots
    print("\n📸 Capturing HTML snapshots...\n")
    try:
        snapshots = await capture_workflow_snapshots()
        print(f"✅ Captured {len(snapshots)} snapshots")
    except Exception as e:
        print(f"⚠️  Snapshot capture failed: {e}")
        snapshots = {}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = (
        f"/workspaces/autouattest/agents/logs/"
        f"license_discovery_{timestamp}.json"
    )
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    discovery = {
        "agent": "license_validator_explorer",
        "target": TARGET_URL,
        "timestamp": timestamp,
        "license_data": TESTABLE_LICENSES,
        "agent_findings": str(agent_result),
        "html_snapshots": snapshots
    }

    with open(log_path, "w") as f:
        json.dump(discovery, f, indent=2)

    # Save context for future agents
    context_path = (
        "/workspaces/autouattest/agents/context/"
        "license_validator_context.json"
    )
    os.makedirs(os.path.dirname(context_path), exist_ok=True)
    with open(context_path, "w") as f:
        json.dump({
            "description": "License validator workflow context",
            "last_updated": timestamp,
            "applicant_details_url": snapshots.get(
                'applicant_details_url', 'unknown'
            ),
            "application_template_url": snapshots.get(
                'application_template_url', 'unknown'
            ),
            "template_options_sample": snapshots.get(
                'template_options_found', []
            ),
            "agent_findings": str(agent_result),
            "html_snapshots": {
                k: v for k, v in snapshots.items()
                if k in [
                    'applicant_details_page',
                    'after_cslb_load',
                    'application_template_page'
                ]
            }
        }, f, indent=2)

    print(f"\n✅ Discovery log saved to {log_path}")
    print(f"✅ Context saved to {context_path}")
    print("\n--- Agent Findings ---")
    print(agent_result)

    return log_path


if __name__ == "__main__":
    asyncio.run(run_license_explorer())