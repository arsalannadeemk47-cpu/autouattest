import asyncio
import os
import glob
import sys
sys.path.insert(0, '/workspaces/autouattest/agents/license_validator')
from run_license_explorer import run_license_explorer
from generate_license_tests import generate_license_tests

AUTH_STATE = "/workspaces/autouattest/tests/setup/.auth/user.json"


def get_latest_license_log():
    logs = glob.glob(
        "/workspaces/autouattest/agents/logs/license_discovery_*.json"
    )
    if logs:
        latest = max(logs)
        print(f"♻️  Reusing existing license log: {latest}")
        return latest
    return None


def clear_previous_logs():
    logs = glob.glob(
        "/workspaces/autouattest/agents/logs/license_discovery_*.json"
    )
    for log in logs:
        os.remove(log)
        print(f"🗑️  Deleted old log: {log}")

    context_path = (
        "/workspaces/autouattest/agents/context/"
        "license_validator_context.json"
    )
    if os.path.exists(context_path):
        os.remove(context_path)
        print(f"🗑️  Deleted old context: {context_path}")


async def check_auth():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=AUTH_STATE)
        page = await context.new_page()
        await page.goto("https://lacps--uat.sandbox.my.site.com/s/")
        await page.wait_for_load_state(
            'domcontentloaded', timeout=30000
        )
        await page.wait_for_timeout(3000)

        authenticated = False
        try:
            btn = page.locator(
                'button[aria-label*="User Profile"]'
            ).first
            authenticated = await btn.is_visible(timeout=5000)
        except Exception:
            pass

        await browser.close()
        return authenticated


async def run_license_pipeline(force_explore: bool = False):
    print("=" * 50)
    print("🚀 Starting license validator pipeline")
    print("=" * 50)

    # Auth check
    print("\n🔍 Step 0: Verifying authentication...")
    is_auth = await check_auth()
    if not is_auth:
        print("\n🔴 Pipeline aborted — not authenticated")
        print("   Refresh cookies and try again")
        return
    print("🟢 Authentication confirmed\n")

    # Stage 1
    log_path = None
    if force_explore:
        print("📍 Stage 1: Clearing previous logs and re-exploring")
        clear_previous_logs()
    else:
        log_path = get_latest_license_log()

    if not log_path:
        print("\n📍 Stage 1: Autonomous workflow exploration")
        log_path = await run_license_explorer()
    else:
        print("\n📍 Stage 1: Skipping — using cached log")

    if not log_path:
        print("🔴 Exploration failed — aborting")
        return

    # Stage 2
    print("\n📍 Stage 2: Generating license validator tests")
    generate_license_tests(log_path)

    # Stage 3
    print("\n📍 Stage 3: Running license validator tests")
    os.system(
        "cd /workspaces/autouattest && "
        "npx playwright test tests/license-validator.auth.spec.ts "
        "--project=chromium-auth --reporter=list"
    )

    print("\n" + "=" * 50)
    print("✅ License validator pipeline complete")
    print("Run 'npx playwright show-report' to see full results")
    print("=" * 50)


if __name__ == "__main__":
    force = len(sys.argv) > 1 and sys.argv[1] == "explore"
    asyncio.run(run_license_pipeline(force_explore=force))


    # Auto-publish report to GitHub Pages
import shutil
shutil.copy(
    '/workspaces/autouattest/license-report/index.html',
    '/workspaces/autouattest/docs/index.html'
)
os.system(
    'cd /workspaces/autouattest && '
    'git add docs/index.html && '
    'git commit -m "Update license validator report $(date +%Y-%m-%d)" && '
    'git push'
)
print("🌐 Report published to GitHub Pages")