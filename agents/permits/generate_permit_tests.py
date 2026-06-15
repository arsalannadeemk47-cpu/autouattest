import json
import os
import sys
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

SEARCH_ADDRESS = "201 N Figueroa St"
TEST_PERMIT = "21041-20000-72305"

def generate_permit_tests(log_path: str):
    with open(log_path, "r") as f:
        discovery_log = json.load(f)

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Extract snapshots separately to give Claude clear instructions
    html_snapshots = discovery_log.get("html_snapshots", {})
    agent_findings = discovery_log.get("agent_findings", "")

    prompt = f"""
    An autonomous agent explored a permit search workflow and
    captured both a findings log and real HTML snapshots at each
    key page state.

    Agent findings:
    {agent_findings}

    HTML snapshots captured at each stage:
    - Homepage: {html_snapshots.get('homepage', 'not captured')[:3000]}
    - Permit search page: {html_snapshots.get('permit_search_page', 'not captured')[:5000]}
    - Search results: {html_snapshots.get('search_results', 'not captured')[:8000]}
    - Permit detail: {html_snapshots.get('permit_detail', 'not captured')[:5000]}

    Using the REAL HTML above, generate a Playwright TypeScript
    test suite. For every selector you write:
    1. First look at the actual HTML to find stable attributes:
       - aria-label, title, placeholder, name, role, type
       - Visible text content inside spans, buttons, labels
    2. Prefer in this order:
       - getByLabel() for form inputs
       - getByRole() with name for buttons and links
       - locator('span[title="exact text"]') for table headers
       - getByText() for visible text
    3. NEVER use dynamic IDs (e.g. input-37, help-message-39)
    4. NEVER use generated class names with random characters
    5. If a column header span has title="Permit Number" use
       locator('span[title="Permit Number"]')
    6. Use toBeAttached() instead of toBeVisible() for elements
       inside scrollable/clipped containers like table headers

    The search address used was: "{SEARCH_ADDRESS}"
    The test permit number is: "{TEST_PERMIT}"

    Include ALL of these test cases:

    1. NAVIGATION — Permit search is findable from homepage
       - Visit the homepage
       - Verify the permit search entry point exists and is visible
       - Click it and verify the search page/panel loads

    2. SUCCESSFUL SEARCH — Address search returns results
       - Navigate to permit search
       - Enter "{SEARCH_ADDRESS}" in the search field
       - Submit the search
       - Verify a list of results appears
       - Verify results contain expected columns (use what the
         agent actually found)

    3. RESULTS FORMAT — Results list contains correct data fields
       - Verify each result row shows a permit number
       - Verify each result row shows a date
       - Verify each result row shows a status

    4. SPECIFIC PERMIT — Test permit appears in results
       - Search for "{SEARCH_ADDRESS}"
       - Verify permit number "{TEST_PERMIT}" appears in the
         results list

    5. PERMIT DETAIL — Clicking permit opens detail page
       - Search for "{SEARCH_ADDRESS}"
       - Find permit "{TEST_PERMIT}" and click it
       - Verify a detail page or panel opens
       - Verify the URL changes or a detail view appears
       - Verify the permit number "{TEST_PERMIT}" is visible
         on the detail page

    6. EMPTY SEARCH — Submitting empty search is handled
       - Navigate to permit search
       - Submit without entering anything
       - Verify an appropriate message or validation appears

    7. NO RESULTS — Search with gibberish address
       - Search for "ZZZZZZ99999 Fake St"
       - Verify a no results message appears rather than an error

    8. SEARCH RESET — Searching again after a result
       - Complete a successful search
       - Clear the search field and enter a different address
       - Verify new results load correctly

    Requirements:
    - Use Playwright Test syntax with proper expect() assertions
    - Use ONLY selectors and URLs the agent actually discovered
    - No login required — this is a public page
    - Add a descriptive comment above each test
    - Include a beforeEach that navigates to the permit search page
      using the exact navigation path the agent discovered
    - Use a reasonable timeout (15000ms) for search results to load
    - Return only the TypeScript code, no explanation
    """

    print("🧠 Generating permit tests from discovery log...\n")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    test_content = response.content[0].text

    # Strip markdown code fences if present
    test_content = test_content.strip()
    if test_content.startswith("```"):
        test_content = test_content.split("\n", 1)[1]
    if test_content.endswith("```"):
        test_content = test_content.rsplit("\n", 1)[0]
    test_content = test_content.strip()

    test_path = "/workspaces/autouattest/tests/permit-search.spec.ts"
    os.makedirs(os.path.dirname(test_path), exist_ok=True)

    with open(test_path, "w") as f:
        f.write(test_content)

    print(f"✅ Tests generated and saved to {test_path}")
    print("\n--- Generated Test File ---")
    print(test_content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_permit_tests.py <path-to-log>")
        sys.exit(1)

    generate_permit_tests(sys.argv[1])