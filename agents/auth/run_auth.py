import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from browser_use import Agent
from browser_use.llm import ChatAnthropic

load_dotenv()

TARGET_URL = "https://lacps--uat.sandbox.my.site.com/s/"
EMAIL = os.getenv("TEST_EMAIL")
PASSWORD = os.getenv("TEST_PASSWORD")

async def run_auth_agent():
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    agent = Agent(
        task=f"""
        You are a test automation agent. Your goal is to authenticate
        on a website entirely on your own.

        Target site: {TARGET_URL}
        Credentials:
          - Email: {EMAIL}
          - Password: {PASSWORD}

        Instructions:
        1. Navigate to the site
        2. Find the login entry point yourself — look for buttons or
           links with text like 'Log In', 'Sign In', or similar
        3. Work through whatever authentication flow you discover —
           it may be multi-step
        4. Complete authentication and confirm you reached an
           authenticated state
        5. Record a detailed log of:
           - Every URL you visited
           - What changed on the page after each action
           - The final URL and page state after authentication
        6. Return the log as a JSON object

        Important: Do not assume the flow. Observe each page state
        before deciding your next action.
        """,
        llm=llm,
        use_vision=False,
        max_failures=3,
        max_actions_per_step=3,
        max_history_items=10,
        calculate_cost=True,
    )

    print("🤖 Auth agent starting — watching it work...\n")
    result = await agent.run(max_steps=15)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"agents/logs/auth_discovery_{timestamp}.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "w") as f:
        json.dump({
            "agent": "auth",
            "target": TARGET_URL,
            "timestamp": timestamp,
            "result": str(result)
        }, f, indent=2)

    print(f"\n✅ Auth flow discovered. Log saved to {log_path}")
    print("\n--- Discovery Result ---")
    print(result)

    return log_path

if __name__ == "__main__":
    asyncio.run(run_auth_agent())