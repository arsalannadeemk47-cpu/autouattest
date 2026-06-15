import asyncio
import os
import glob


def get_latest_log():
    logs = glob.glob("agents/logs/arsalan_discovery_*.json")
    if logs:
        latest = max(logs)
        print(f"♻️  Reusing existing discovery log: {latest}")
        return latest
    return None

async def run_full_pipeline(force_explore: bool = False):
    print("=" * 50)
    print("🚀 Starting autonomous test generation pipeline")
    print("=" * 50)

    # Stage 1: Check for existing log or run agent
    log_path = None

    if not force_explore:
        log_path = get_latest_log()

    if not log_path:
        print("\n📍 Stage 1: Autonomous site exploration")
        log_path = await run_arsalan_agent()
    else:
        print("\n📍 Stage 1: Skipping exploration — using cached log")
        print("   (run with force_explore=True to re-explore)")

    # Stage 2: Generate tests from discovery log
    print("\n📍 Stage 2: Generating tests from discoveries")
    generate_arsalan_tests(log_path)

    # Stage 3: Run the generated tests
    print("\n📍 Stage 3: Running generated tests")
    os.system(
    "cd /workspaces/autouattest && "
    "npx playwright test tests/auth.spec.ts "
    "--reporter=list"
    )

    print("\n" + "=" * 50)
    print("✅ Pipeline complete")
    print("Run 'npx playwright show-report' to see full results")
    print("=" * 50)

if __name__ == "__main__":
    import sys
    # Pass "explore" argument to force a fresh exploration
    # e.g. python run_pipeline.py explore
    force = len(sys.argv) > 1 and sys.argv[1] == "explore"
    asyncio.run(run_full_pipeline(force_explore=force))