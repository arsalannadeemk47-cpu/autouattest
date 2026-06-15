import asyncio
import os
import glob
from permits.run_permit_explorer import run_permit_explorer
from permits.generate_permit_tests import generate_permit_tests

def get_latest_permit_log():
    logs = glob.glob("/workspaces/autouattest/agents/logs/permit_discovery_*.json") + \
           glob.glob("/workspaces/autouattest/agents/logs/arsalan_discovery_*.json")
    if logs:
        latest = max(logs)
        print(f"♻️  Reusing existing permit log: {latest}")
        return latest
    return None

async def run_permit_pipeline(force_explore: bool = False):
    print("=" * 50)
    print("🚀 Starting permit search pipeline")
    print("=" * 50)

    # Stage 1: Explore or reuse cached log
    log_path = None

    if not force_explore:
        log_path = get_latest_permit_log()

    if not log_path:
        print("\n📍 Stage 1: Autonomous permit search exploration")
        log_path = await run_permit_explorer()
    else:
        print("\n📍 Stage 1: Skipping exploration — using cached log")

    # Stage 2: Generate tests
    print("\n📍 Stage 2: Generating permit tests from discoveries")
    generate_permit_tests(log_path)

    # Stage 3: Run the generated tests
    print("\n📍 Stage 3: Running permit tests")
    os.system(
    "cd /workspaces/autouattest && "
    "npx playwright test tests/permit-search.spec.ts "
    "--reporter=list"
    )

    print("\n" + "=" * 50)
    print("✅ Permit pipeline complete")
    print("Run 'npx playwright show-report' to see full results")
    print("=" * 50)

if __name__ == "__main__":
    import sys
    force = len(sys.argv) > 1 and sys.argv[1] == "explore"
    asyncio.run(run_permit_pipeline(force_explore=force))

