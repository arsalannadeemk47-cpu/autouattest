import { test, expect, Page } from '@playwright/test';

test.use({ storageState: 'tests/setup/.auth/user.json' });

// Source of truth: license_code_permit_validations.xlsx
// C35 and C39 excluded — no license number available
const LICENSE_TEST_DATA = [
  { license: '1045907', code: 'A',   expectedPermits: ['Plumbing', 'Pressure Vessel'] },
  { license: '1092820', code: 'B',   expectedPermits: ['Bldg-Alter/Repair', 'Electrical', 'EV Charger', 'HVAC', 'Plumbing', 'Pressure Vessel'] },
  { license: '1044490', code: 'C-4', expectedPermits: ['Pressure Vessel'] },
  { license: '1000061', code: 'C-7', expectedPermits: ['Electrical'] },
  { license: '1057929', code: 'C-9',  expectedPermits: ['Bldg-Alter/Repair'] },
  { license: '1045907', code: 'C10', expectedPermits: ['Electrical', 'EV charger', 'Pressure Vessel'] },
  { license: '808879',  code: 'C11', expectedPermits: ['Elevator', 'Pressure Vessel'] },
  { license: '1042659', code: 'C16', expectedPermits: ['Fire Sprinkler', 'Pressure Vessel'] },
  { license: '1000169', code: 'C20', expectedPermits: ['Electrical', 'HVAC', 'Pressure Vessel'] },
  { license: '1001177', code: 'C34', expectedPermits: ['Pressure Vessel'] },
  { license: '1000098', code: 'C36', expectedPermits: ['Plumbing', 'Pressure Vessel'] },
  { license: '999993',  code: 'C38', expectedPermits: ['Electrical', 'Pressure Vessel'] },
  { license: '1006709', code: 'C42', expectedPermits: ['Pressure Vessel'] },
  { license: '1071509', code: 'C43', expectedPermits: ['HVAC'] },
  { license: '1000366', code: 'C46', expectedPermits: ['Plumbing'] },
  { license: '1015870', code: 'C55', expectedPermits: ['Pressure Vessel'] },
  { license: '957084',  code: 'C61', expectedPermits: ['Pressure Vessel'] },
  { license: '1084182', code: 'D21', expectedPermits: ['Pressure Vessel'] },
  { license: '1000868', code: 'D34', expectedPermits: ['Pressure Vessel'] },
  { license: '1001661', code: 'D35', expectedPermits: ['Pressure Vessel'] },
  { license: '943773',  code: 'D40', expectedPermits: ['Pressure Vessel'] }
];

// ─── Navigation helper ────────────────────────────────────────────────────────

async function navigateToApplicantDetails(page: Page): Promise<void> {
  // Step 1: Homepage
  await page.goto('https://lacps--uat.sandbox.my.site.com/s/');
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(2000);

  // Step 2: Open Permits menu
  await page.getByRole('button', { name: /permits/i }).click();
  await page.waitForTimeout(1500);

  // Step 3: New Permit Application
  await page.getByRole('link', { name: 'New Permit Application' }).click();
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);

  // Step 4: Start New Application
  await page.getByRole('button', { name: 'Start New Application' }).click();
  await page.waitForTimeout(3000);

  // Step 5: Select Pre-Defined Scope
  // Salesforce visual picker — MUST click the label, not the input
  await page.locator('label[for*="Pre-Defined"][for*="Scope"]').click();
  await page.waitForTimeout(3000);

  // Step 6: Select Address radio
  // Standard radio — use evaluate() to bypass label pointer interception
  await page.locator('input[value="choiceAddress"]').evaluate(
    (el: HTMLInputElement) => el.click()
  );
  await page.waitForTimeout(2000);

  // Step 7: Type address to trigger Salesforce autocomplete
  // MUST use pressSequentially — fill() does not fire keyboard events
  const addressInput = page.locator('input[placeholder="Search Addresses..."]');
  await addressInput.click();
  await page.waitForTimeout(500);
  await addressInput.pressSequentially('3761 S Du', { delay: 100 });
  await page.waitForTimeout(3000);

  // Step 8: Select address from autocomplete listbox
  // Scope to the address combobox dropdown specifically to avoid
  // matching the site search listbox in the header
  await page.waitForSelector(
    'input[placeholder="Search Addresses..."] ~ * [role="option"], ' +
    '#dropdown-element-356 [role="option"], ' +
    'lightning-base-combobox [role="option"]',
    { timeout: 15000 }
  );
  await page.locator('lightning-base-combobox [role="option"]')
    .filter({ hasText: '3761 S Dunn Dr' })
    .first()
    .click();


  // Step 9: Next (past address screen)
  await page.getByRole('button', { name: 'Next' }).last().click();
  await page.waitForTimeout(3000);

  // Step 10: Next (past second screen — arrives at Applicant Details)
  await page.getByRole('button', { name: 'Next' }).last().click();
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);
}

// ─── Template options helper ──────────────────────────────────────────────────

async function getTemplateOptions(page: Page): Promise<string[]> {
  // Wait for the Application Template fieldset to render
  await page.waitForSelector(
    'fieldset:has(legend:has-text("Application Template"))',
    { timeout: 15000 }
  );
  await page.waitForTimeout(1000);

  // Drill into the exact label spans inside the radio group
  // Confirmed selector from live HTML inspection
  const labels = await page.locator(
    'fieldset:has(legend:has-text("Application Template")) ' +
    '.slds-form-element__label lightning-formatted-rich-text ' +
    'span[part="formatted-rich-text"]'
  ).allTextContents();

  return labels
    .map(t => t.trim())
    .filter(t => t.length > 0 && t.toLowerCase() !== 'application template');
}

// ─── Tests ────────────────────────────────────────────────────────────────────

test.describe('License Validator Tests', () => {
  for (const testData of LICENSE_TEST_DATA) {
    test(`License ${testData.code} - should show correct permit types`, async ({ page }) => {

      // Navigate to Applicant Details
      await navigateToApplicantDetails(page);

      // Select Applicant Role: Contractor
      // This field is a native <select> wrapped in lightning-select — selectOption works
      await page.locator('select[name="Applicant_Role"]').selectOption({ label: 'Contractor' });
      await page.waitForTimeout(1500);

      // Select "Existing License On My Account" radio
      // Standard radio — use evaluate() to bypass label interception
      await page.locator('input[value="ExistingLicense"]').evaluate(
        (el: HTMLInputElement) => el.click()
      );
      await page.waitForTimeout(1500);

      // Open Existing License Number combobox and select by data-value
      await page.locator('button[aria-label="Existing License Number"]').click();
      await page.waitForTimeout(1000);
      await page.locator(`lightning-base-combobox-item[data-value="${testData.license}"]`).click();
      await page.waitForTimeout(1500);

      // Open Existing License Type combobox and select by data-value
      await page.locator('button[aria-label="Existing License Type"]').click();
      await page.waitForTimeout(1000);
      await page.locator(`lightning-base-combobox-item[data-value="${testData.code}"]`).click();
      await page.waitForTimeout(1500);

      // Click Load From CSLB and wait for success confirmation
      await page.getByRole('button', { name: /load from cslb/i }).click();
      await page.getByText('Successfully loaded!').waitFor({ timeout: 30000 });
      await page.waitForTimeout(1000);

      // Next → Application Template page
      await page.getByRole('button', { name: 'Next' }).last().click();
      await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
      await page.waitForTimeout(3000);

      // Collect visible permit options
      const visiblePermits = await getTemplateOptions(page);

      // Normalize for case-insensitive comparison
      const normalize = (s: string) => s.toLowerCase().trim();
      const normalizedExpected = testData.expectedPermits.map(normalize);
      const normalizedVisible  = visiblePermits.map(normalize);

      // Determine mismatches
      const missingPermits = testData.expectedPermits.filter(
        p => !normalizedVisible.includes(normalize(p))
      );
      const unexpectedPermits = visiblePermits.filter(
        p => !normalizedExpected.includes(normalize(p))
      );

      // Log in format the reporter's regex can parse
      console.log(`\n=== License ${testData.code} (${testData.license}) ===`);
      console.log(`Expected permits: ${testData.expectedPermits.join(', ')}`);
      console.log(`Visible permits: ${visiblePermits.join(', ')}`);
      if (missingPermits.length > 0) {
        console.log(`❌ Missing permits: ${missingPermits.join(', ')}`);
      }
      if (unexpectedPermits.length > 0) {
        console.log(`❌ Unexpected permits: ${unexpectedPermits.join(', ')}`);
      }
      if (missingPermits.length === 0 && unexpectedPermits.length === 0) {
        console.log(`✅ All permits match!`);
      }

      // Assertions
      expect(
        missingPermits,
        `Missing permits for license ${testData.code}: ${missingPermits.join(', ')}`
      ).toEqual([]);

      expect(
        unexpectedPermits,
        `Unexpected permits for license ${testData.code}: ${unexpectedPermits.join(', ')}`
      ).toEqual([]);
    });
  }
});