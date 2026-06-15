import asyncio
import os
import glob
import sys
from profile.run_profile_explorer import run_profile_explorer
from profile.generate_profile_tests import generate_profile_tests

# Add the project root to path so we can import verify_auth
sys.path.append('/workspaces/autouattest')

async def check_auth():
    """Run cookie verification and return True if authenticated."""
    from tests.setup.verify_auth import verify_cookies
    return await verify_cookies()

def get_latest_profile_log():
    logs = glob.glob(
        "/workspaces/autouattest/agents/logs/profile_discovery_*.json"
    )
    if logs:
        latest = max(logs)
        print(f"♻️  Reusing existing profile log: {latest}")
        return latest
    return None

def clear_previous_logs():
    """Delete all previous profile discovery logs."""
    logs = glob.glob(
        "/workspaces/autouattest/agents/logs/profile_discovery_*.json"
    )
    for log in logs:
        os.remove(log)
        print(f"🗑️  Deleted old log: {log}")

    # Also clear the cached context file
    context_path = "/workspaces/autouattest/agents/context/profile_context.json"
    if os.path.exists(context_path):
        os.remove(context_path)
        print(f"🗑️  Deleted old context: {context_path}")

async def run_profile_pipeline(force_explore: bool = False):
    print("=" * 50)
    print("🚀 Starting profile settings pipeline")
    print("=" * 50)

    # Always verify auth first before doing anything
    print("\n🔍 Step 0: Verifying authentication...")
    auth_result = await check_auth()

    if auth_result is False:
        print("\n🔴 Pipeline aborted — not authenticated.")
        print("   Refresh your cookies and try again.")
        return

    if auth_result is None:
        print("\n🟡 Authentication uncertain.")
        print("   Check screenshot at:")
        print("   tests/setup/auth_check.png")
        response = input("\n   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Pipeline aborted.")
            return

    print("\n🟢 Authentication confirmed — proceeding\n")

    # Stage 1: Explore or reuse cached log
    log_path = None

    if force_explore:
        print("📍 Stage 1: Clearing previous logs and re-exploring")
        clear_previous_logs()
    else:
        log_path = get_latest_profile_log()

    if not log_path:
        print("\n📍 Stage 1: Autonomous profile exploration")
        log_path = await run_profile_explorer()
    else:
        print("\n📍 Stage 1: Skipping exploration — using cached log")

    # Stage 2: Generate tests
    print("\n📍 Stage 2: Generating profile tests")
    generate_profile_tests(log_path)

    # Stage 3: Run tests
    print("\n📍 Stage 3: Running profile tests")
    os.system(
        "cd /workspaces/autouattest && "
        "npx playwright test tests/profile-settings.auth.spec.ts "
        "--project=chromium-auth --reporter=list"
    )

    print("\n" + "=" * 50)
    print("✅ Profile pipeline complete")
    print("Run 'npx playwright show-report' to see full results")
    print("=" * 50)

if __name__ == "__main__":
    import sys
    force = len(sys.argv) > 1 and sys.argv[1] == "explore"
    asyncio.run(run_profile_pipeline(force_explore=force))