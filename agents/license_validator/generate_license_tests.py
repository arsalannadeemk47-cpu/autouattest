import json
import os
import sys
from turtle import delay
from dotenv import load_dotenv
from anthropic import Anthropic
from license_data import TESTABLE_LICENSES

load_dotenv()

TARGET_URL = "https://lacps--uat.sandbox.my.site.com/s/"
SEARCH_ADDRESS = "3761"
SELECT_ADDRESS = "3761 S Dunn Dr"


def generate_license_tests(log_path: str):
    with open(log_path, "r") as f:
        discovery_log = json.load(f)

    # Load context if available
    context_path = (
        "/workspaces/autouattest/agents/context/"
        "license_validator_context.json"
    )
    context = {}
    if os.path.exists(context_path):
        with open(context_path, "r") as f:
            context = json.load(f)

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    html_snapshots = discovery_log.get("html_snapshots", {})
    agent_findings = discovery_log.get("agent_findings", "")

    # Build the license test cases as a formatted string
    license_cases = "\n".join([
        f"  - License: {l['license_number']}, "
        f"Code: {l['license_code']}, "
        f"Expected permits: {l['permits']}"
        for l in TESTABLE_LICENSES
    ])

    prompt = f"""
    An autonomous agent explored a permit application workflow and
    captured HTML snapshots and findings.

    Agent findings:
    {agent_findings}

    Saved context:
    {json.dumps(context, indent=2)}

    HTML snapshots:
    - Homepage: {str(html_snapshots.get('homepage', ''))[:1000]}
    - New permit page: {str(html_snapshots.get('new_permit_page', ''))[:2000]}
    - Applicant details: {str(html_snapshots.get('applicant_details_page', ''))[:5000]}
    - After CSLB load: {str(html_snapshots.get('after_cslb_load', ''))[:3000]}
    - Application template page: {str(html_snapshots.get('application_template_page', ''))[:5000]}


    CONFIRMED WORKING SELECTORS for this site:
    These selectors have been verified to work — use them exactly:
        // Navigation to permit application
        await page.getByRole('button', {{ name: /permits/i }}).click();
        await page.getByRole('link', {{ name: 'New Permit Application' }}).click();
        await page.getByRole('button', {{ name: 'Start New Application' }}).click();

        // Pre-Defined Scope — MUST click the label, NOT the input radio
        // The label intercepts pointer events in Salesforce visual picker
        await page.locator('label[for*="Pre-Defined"][for*="Scope"]').click();
        await page.waitForTimeout(3000);

      // Select Address radio — use evaluate() to bypass label pointer interception
        // The input value is "choiceAddress" which is stable unlike the dynamic ID
        await page.locator('input[value="choiceAddress"]').evaluate(
        (el: HTMLInputElement) => el.click()
        );
        await page.waitForTimeout(2000);

        // Address search — MUST use pressSequentially to trigger Salesforce autocomplete
        // fill() does not fire keyboard events so the dropdown will not appear
        await page.locator('input[placeholder="Search Addresses..."]').click();
        await page.waitForTimeout(500);
        await page.locator('input[placeholder="Search Addresses..."]').pressSequentially('3761 S D', { delay: 100 });
        await page.waitForTimeout(3000);

        // Select from Salesforce listbox dropdown
        await page.locator('[role="listbox"] [role="option"]')
       .filter({{ hasText: '3761 S Dunn Dr' }})
       .first()
       .click();

        await page.getByRole('button', {{ name: 'Next' }}).last().click();
        await page.waitForTimeout(3000);
        await page.getByRole('button', {{ name: 'Next' }}).last().click();

        // Applicant details
        await page.getByLabel(/applicant role/i).selectOption('Contractor');
        await page.getByText('Existing License on my account').click();
       // Existing License radio — evaluate to bypass label intercept
        await page.locator('input[value="ExistingLicense"]').evaluate(
        (el: HTMLInputElement) => el.click()
        );
        await page.waitForTimeout(1500);

    // License number is a combobox dropdown, NOT a text input — click to open then select
        await page.locator('button[aria-label="Existing License Number"]').click();
        await page.waitForTimeout(1000);
        await page.locator(`lightning-base-combobox-item[data-value="${licenseNumber}"]`).click();
        await page.waitForTimeout(1500);

        // License type is ALSO a combobox dropdown, NOT a select element
        await page.locator('button[aria-label="Existing License Type"]').click();
        await page.waitForTimeout(1000);
        await page.locator(`lightning-base-combobox-item[data-value="${licenseCode}"]`).click();
        await page.waitForTimeout(1500);
        
        await page.getByRole('button', {{ name: /load from cslb/i }}).click();
        await page.getByText('Successfully loaded!').waitFor({{ timeout: 30000 }});
        await page.getByRole('button', {{ name: 'Next' }}).last().click();


    License test data (from spreadsheet):
{license_cases}

    Generate a complete Playwright TypeScript test suite that:

    1. Uses storageState: 'tests/setup/.auth/user.json' for auth
    2. Has a shared beforeEach that navigates through steps 1-6:
       - Go to {TARGET_URL}
       - Click Permits menu → New Permit Application
       - Click Start New Application
       - Select Pre-Defined Scope
        - Address radio button: page.locator('label[for*="Address"]')
         MUST be clicked BEFORE typing in the address search field
       - Address search input: use getByPlaceholder or getByRole textbox
         only AFTER clicking the Address radio button
       - Type "{SEARCH_ADDRESS}" in address search
       - Select "{SELECT_ADDRESS}" from dropdown
       - Click Next
       - Wait for the page to load ( or about 3-4 seconds)
       - Click Next again
       (arrive at Applicant Details page)
    3. Creates ONE test per license code in the test data above
    4. Each test should:
       a. Select "Contractor" from Applicant Role dropdown
       b. Select "Existing License on my account"
       c. Fill in the license number for that test case
       d. Select the corresponding license code/type
       e. Click "Load From CSLB"
       f. Wait for "Successfully loaded!" text to appear
          (use timeout of 30000ms)
       g. Click Next
       h. On the Application Template page, get ALL visible
          permit/template option texts
       i. Compare against the expected permits for this license
       j. FAIL if any expected permit is missing from the page
       k. FAIL if any unexpected permit appears on the page
       l. Log clearly which permits are missing and which are extra
    5. Name each test descriptively:
       "License [CODE] - should show correct permit types"
    6. Use a helper function to navigate to applicant details
       to avoid duplicating the beforeEach navigation code
    7. Use a helper function to get all template options from the page
    8. Add a 3000ms timeout between major navigation steps
    9. Use these EXACT selectors that are confirmed to work on this site:
       - Pre-Defined Scope radio: MUST click the label, not the input,
         because the label intercepts pointer events in Salesforce
         visual picker components:
         page.locator('label[for*="Pre-Defined"][for*="Scope"]')
       - Start New Application button:
         page.getByRole('button', {{ name: 'Start New Application' }})
       - Permits menu:
         page.getByRole('button', {{ name: /permits/i }})
       - New Permit Application link:
         page.getByRole('link', {{ name: 'New Permit Application' }})
    10. NEVER use waitForLoadState('networkidle') — use
       waitForLoadState('domcontentloaded', {{ timeout: 30000 }})
       or waitForTimeout(3000) instead
    11. Use selectors based on what the agent actually found —
        getByRole, getByLabel, getByText — never dynamic IDs

    The test file should be self-contained and runnable with:
    npx playwright test tests/license-validator.auth.spec.ts
    --project=chromium-auth

    Return only TypeScript code, no explanation.
    """

    print("🧠 Generating license validator tests...\n")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
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

    test_path = (
        "/workspaces/autouattest/tests/"
        "license-validator.auth.spec.ts"
    )
    os.makedirs(os.path.dirname(test_path), exist_ok=True)

    with open(test_path, "w") as f:
        f.write(test_content)

    print(f"✅ Tests saved to {test_path}")
    print("\n--- Generated Test File ---")
    print(test_content)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python generate_license_tests.py "
            "<path-to-log>"
        )
        sys.exit(1)
    generate_license_tests(sys.argv[1])