import json
import os
import sys
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

def generate_auth_tests(log_path: str):
    with open(log_path, "r") as f:
        discovery_log = json.load(f)

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""
    An autonomous agent explored an authentication flow on a website
    and produced this discovery log:

    {json.dumps(discovery_log, indent=2)}

    Based ONLY on what the agent discovered — the real elements it
    found, the actual URLs, the real button text and field labels —
    generate a simple Playwright TypeScript test suite.

    Include these test cases:
    1. Successful authentication (happy path)
    2. Invalid email format
    3. Valid email but wrong password
    4. Empty password field submission
    5. Verify redirect URL after successful auth matches what
       the agent found
    6. Verify an element visible only to authenticated users exists
       after login

    Requirements:
    - Use Playwright Test syntax with proper expect() assertions
    - Use the real selectors and text the agent discovered,
      not assumptions
    - Use environment variables for credentials
      (process.env.TEST_EMAIL etc)
    - Add a descriptive comment above each test explaining
      what it covers
    - Include a beforeEach that navigates to the login page
    - Return only the TypeScript code, no explanation
    """

    print("🧠 Generating tests from discovery log...\n")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    test_content = response.content[0].text
    test_path = "tests/agents/auth/auth.spec.ts"
    os.makedirs(os.path.dirname(test_path), exist_ok=True)

    with open(test_path, "w") as f:
        f.write(test_content)

    print(f"✅ Tests generated and saved to {test_path}")
    print("\n--- Generated Test File ---")
    print(test_content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_tests.py <path-to-discovery-log>")
        sys.exit(1)

    generate_auth_tests(sys.argv[1])