import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from browser_use import Agent
from browser_use.llm import ChatAnthropic

load_dotenv()

TARGET_URL = "https://lacps--uat.sandbox.my.site.com/s/"
SEARCH_ADDRESS = "201 N Figueroa St"
TEST_PERMIT = "21041-20000-72305"

async def run_permit_explorer():
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    agent = Agent(
        task=f"""
        You are a test automation agent exploring a permit search
        workflow on a website. Do not assume anything about the
        site structure — observe each page state before acting.

        Target site: {TARGET_URL}
        Search address: {SEARCH_ADDRESS}
        Test permit number: {TEST_PERMIT}

        Instructions:
        1. Navigate to the site homepage
        2. Find the "Permit Search" option on the homepage —
           it may be a link, button, card, or menu item.
           Look for text like "Permit Search", "Search Permits",
           "Permits", or similar. Do not assume where it is.
        3. Click it and observe what page or panel loads
        4. Find the search input and enter the address:
           "{SEARCH_ADDRESS}"
        5. Submit the search and observe the results
        6. Record everything about the results page:
           - The URL
           - Column headers in the results list
           - What data is shown per permit (number, date, status etc)
           - How many results appeared
           - The exact text and format of permit numbers shown
        7. Find permit number "{TEST_PERMIT}" in the results
           if it appears, and click on it
        8. Record everything about the detail page:
           - The URL
           - All visible fields and their values
           - Any buttons or actions available
        9. Return a detailed JSON log of every step, every element
           interacted with, every URL visited, and everything
           observed on each page

        Important: Record exact text, selectors, and URLs as you
        find them. Do not summarise or paraphrase what you see.
        """,
        llm=llm,
        use_vision=False,
        max_failures=3,
        max_actions_per_step=3,
        max_history_items=10,
        calculate_cost=True,
    )

    print("🤖 Permit explorer agent starting...\n")
    result = await agent.run(max_steps=25)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"/workspaces/autouattest/agents/logs/permit_discovery_{timestamp}.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "w") as f:
        json.dump({
            "agent": "permit_explorer",
            "target": TARGET_URL,
            "search_address": SEARCH_ADDRESS,
            "test_permit": TEST_PERMIT,
            "timestamp": timestamp,
            "result": str(result)
        }, f, indent=2)

    print(f"\n✅ Permit flow discovered. Log saved to {log_path}")
    print("\n--- Discovery Result ---")
    print(result)

    return log_path

if __name__ == "__main__":
    asyncio.run(run_permit_explorer())