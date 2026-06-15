import json
import os
import sys
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

NEW_ADDRESS = {
    "street": "350 S Bixel St",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90017"
}

def generate_profile_tests(log_path: str):
    with open(log_path, "r") as f:
        discovery_log = json.load(f)

    # Also load saved context if available
    context_path = "/workspaces/autouattest/agents/context/profile_context.json"
    context = {}
    if os.path.exists(context_path):
        with open(context_path, "r") as f:
            context = json.load(f)

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    html_snapshots = discovery_log.get("html_snapshots", {})
    agent_findings = discovery_log.get("agent_findings", "")

    prompt = f"""
    An autonomous agent explored a user profile settings page on an
    authenticated website and captured findings and HTML snapshots.

    Agent findings:
    {agent_findings}

    Saved context from previous explorations:
    {json.dumps(context, indent=2)}

    HTML snapshots:
    - Authenticated homepage:
      {str(html_snapshots.get('homepage_authenticated', ''))[:2000]}
    - Profile menu open:
      {str(html_snapshots.get('profile_menu_open', ''))[:2000]}
    - Profile page:
      {str(html_snapshots.get('profile_page', ''))[:5000]}
    - Profile edit mode:
      {str(html_snapshots.get('profile_edit_mode', ''))[:5000]}
    - Final profile state:
      {str(html_snapshots.get('profile_page_final', ''))[:3000]}

    New address used in testing: {json.dumps(NEW_ADDRESS)}

    Using the REAL HTML and findings above, generate a complete
    Playwright TypeScript test suite for the user profile page.

    The test file must use this storage state for authentication:
    storageState: 'tests/setup/.auth/user.json'

    Include ALL of these test cases:

    1. NAVIGATION — Profile settings is reachable from homepage
       - Click profile icon in top right
       - Click User Settings
       - Verify profile page loads with correct URL

    2. CONTACT INFO VISIBLE — Profile shows contact information
       - Navigate to profile page
       - Verify phone number field is visible
       - Verify email address field is visible
       - Verify address fields are visible

    3. EDIT MODE — Edit button opens editable form
       - Navigate to profile page
       - Click Edit button
       - Verify fields become editable

    4. ADDRESS CHANGE — User can update their address
       - Navigate to profile page
       - Click Edit
       - Clear and fill address fields with:
         Street: {NEW_ADDRESS['street']}
         City: {NEW_ADDRESS['city']}
         State: {NEW_ADDRESS['state']}
         Zip: {NEW_ADDRESS['zip']}
       - Save the changes
       - Verify the new address is displayed

    5. USER TYPE VISIBLE — User type section is present
       - Navigate to profile page
       - Verify the user type/role section exists
       - Verify available and chosen lists are present

    6. MOVE TO CHOSEN — User can add a role
       - Navigate to profile page
       - Find an item in the available list
       - Click move to chosen button
       - Verify item moves to chosen list

    7. MOVE TO AVAILABLE — User can remove a role
       - Navigate to profile page
       - Find an item in the chosen list
       - Click move to available button
       - Verify item moves to available list

    8. SAVE PROFILE — Changes are persisted
       - Make a change to the profile
       - Click Save
       - Reload the page
       - Verify changes persisted

    Selector requirements:
    - Use getByLabel() for form inputs
    - Use getByRole() for buttons and links
    - Use span[title="exact text"] for any clipped headers
    - Use toBeAttached() for elements inside scrollable containers
    - NEVER use dynamic IDs
    -  Use storageState from 'tests/setup/.auth/user.json'
    - NEVER use waitForLoadState('networkidle') — Salesforce sites
      continuously poll and never reach networkidle. Always use
      waitForLoadState('domcontentloaded', {{ timeout: 30000 }})
      or waitForTimeout(3000) instead
    - Name the file to use .auth.spec.ts extension
    - Return only TypeScript code, no explanation
    """

    print("🧠 Generating profile tests from discovery log...\n")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    test_content = response.content[0].text

    # Strip markdown fences
    test_content = test_content.strip()
    if test_content.startswith("```"):
        test_content = test_content.split("\n", 1)[1]
    if test_content.endswith("```"):
        test_content = test_content.rsplit("\n", 1)[0]
    test_content = test_content.strip()

    test_path = "/workspaces/autouattest/tests/profile-settings.auth.spec.ts"
    os.makedirs(os.path.dirname(test_path), exist_ok=True)

    with open(test_path, "w") as f:
        f.write(test_content)

    print(f"✅ Tests saved to {test_path}")
    print("\n--- Generated Test File ---")
    print(test_content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_profile_tests.py <log-path>")
        sys.exit(1)

    generate_profile_tests(sys.argv[1])