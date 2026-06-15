import { test, expect, Page } from '@playwright/test';

test.use({ storageState: 'tests/setup/.auth/user.json' });

interface LicenseTestData {
  code: string;
  number: string;
  expectedPermits: string[];
}

const licenseTestData: LicenseTestData[] = [
  { code: 'A', number: '1045907', expectedPermits: ['Plumbing', 'Pressure Vessel'] },
  { code: 'B', number: '1092820', expectedPermits: ['Bldg-Alter/Repair', 'Electrical', 'EV Charger', 'HVAC', 'Plumbing', 'Pressure Vessel'] },
  { code: 'C-4', number: '1044490', expectedPermits: ['Pressure Vessel'] },
  { code: 'C-7', number: '1002480', expectedPermits: ['Electrical'] },
  { code: 'C9', number: '1057929', expectedPermits: ['Bldg-Alter/Repair'] },
  { code: 'C10', number: '1045907', expectedPermits: ['Electrical', 'EV charger', 'Pressure Vessel'] },
  { code: 'C11', number: '808879', expectedPermits: ['Elevator', 'Pressure Vessel'] },
  { code: 'C16', number: '1042659', expectedPermits: ['Fire Sprinkler', 'Pressure Vessel'] },
  { code: 'C20', number: '1000169', expectedPermits: ['Electrical', 'HVAC', 'Pressure Vessel'] },
  { code: 'C34', number: '1001177', expectedPermits: ['Pressure Vessel'] },
  { code: 'C36', number: '1000098', expectedPermits: ['Plumbing', 'Pressure Vessel'] },
  { code: 'C38', number: '999993', expectedPermits: ['Electrical', 'Pressure Vessel'] },
  { code: 'C42', number: '1006709', expectedPermits: ['Pressure Vessel'] },
  { code: 'C43', number: '1071509', expectedPermits: ['HVAC'] },
  { code: 'C46', number: '1003132', expectedPermits: ['Plumbing'] },
  { code: 'C55', number: '1015870', expectedPermits: ['Pressure Vessel'] },
  { code: 'C61', number: '957084', expectedPermits: ['Pressure Vessel'] },
  { code: 'D34', number: '1101973', expectedPermits: ['Pressure Vessel'] },
  { code: 'D35', number: '1001661', expectedPermits: ['Pressure Vessel'] },
  { code: 'D57', number: '248449', expectedPermits: ['Pressure Vessel'] },
];

/**
 * Navigate to the Applicant Details page through the permit application flow
 */
async function navigateToApplicantDetailsPage(page: Page): Promise<void> {
  // Navigate to home
  await page.goto('https://lacps--uat.sandbox.my.site.com/s/');
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);

  // Click Permits menu
  await page.getByRole('button', { name: /permits/i }).click();
  await page.waitForTimeout(3000);

  // Click New Permit Application
  await page.getByRole('link', { name: 'New Permit Application' }).click();
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);

  // Click Start New Application
  await page.getByRole('button', { name: 'Start New Application' }).click();
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);

  // Select Pre-Defined Scope
  // Click the label since it sits on top of the radio input in Salesforce visual picker
  await page.locator('label[for*="Pre-Defined"][for*="Scope"]').click();
  await page.waitForTimeout(3000);

// Select Address radio — use evaluate to bypass label pointer interception
  await page.locator('input[value="choiceAddress"]').evaluate(
    (el: HTMLInputElement) => el.click()
  );
  await page.waitForTimeout(2000);

// Click the field first to focus it
  await page.locator('input[placeholder="Search Addresses..."]').click();
  await page.waitForTimeout(500);
  
  // Type character by character to trigger Salesforce autocomplete events
  await page.locator('input[placeholder="Search Addresses..."]').pressSequentially('3761 S D', { delay: 100 });
  
  // Wait for the autocomplete dropdown to populate
  await page.waitForTimeout(3000);

// Click the address from the autocomplete listbox
  await page.locator('[role="listbox"] [role="option"]')
    .filter({ hasText: '3761 S Dunn Dr' })
    .first()
    .click();
  await page.waitForTimeout(2000);

  // Click Next (first time)
  await page.getByRole('button', { name: 'Next' }).last().click();
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);

  // Click Next (second time)
  await page.getByRole('button', { name: 'Next' }).last().click();
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  await page.waitForTimeout(3000);
}

async function getTemplateOptions(page: Page): Promise<string[]> {
  // Wait for the Application Template fieldset to be present
  await page.waitForSelector(
    'fieldset:has(legend:has-text("Application Template"))',
    { timeout: 15000 }
  );
  await page.waitForTimeout(1000);

  // Target the label text nested inside the Application Template radio group
  const templateLabels = await page.locator(
    'fieldset:has(legend:has-text("Application Template")) .slds-form-element__label lightning-formatted-rich-text span[part="formatted-rich-text"]'
  ).allTextContents();

  return templateLabels
    .map(t => t.trim())
    .filter(t => t.length > 0 && t.toLowerCase() !== 'application template');
}

// Create a test for each license code
for (const testData of licenseTestData) {
  test(`License ${testData.code} - should show correct permit types`, async ({ page }) => {
    // Navigate to applicant details page
    await navigateToApplicantDetailsPage(page);

    // Select "Contractor" from Applicant Role dropdown
    await page.getByLabel(/applicant role/i).selectOption('Contractor');
    await page.waitForTimeout(1500);

  // Select Existing License radio — use evaluate to bypass label intercept
    await page.locator('input[value="ExistingLicense"]').evaluate(
      (el: HTMLInputElement) => el.click()
    );
    await page.waitForTimeout(1500);

  // Open the Existing License Number combobox dropdown
    await page.locator('button[aria-label="Existing License Number"]').click();
    await page.waitForTimeout(1000);

    // Select the license number from the dropdown by data-value
    await page.locator(`lightning-base-combobox-item[data-value="${testData.number}"]`).click();
    await page.waitForTimeout(1500);

// Open the Existing License Type combobox dropdown
    await page.locator('button[aria-label="Existing License Type"]').click();
    await page.waitForTimeout(1000);

    // Select the license code from the dropdown by data-value
    await page.locator(`lightning-base-combobox-item[data-value="${testData.code}"]`).click();
    await page.waitForTimeout(1500);

    // Click "Load From CSLB"
    await page.getByRole('button', { name: /load from cslb/i }).click();

    // Wait for "Successfully loaded!" text to appear
    await page.getByText('Successfully loaded!').waitFor({ timeout: 30000 });
    await page.waitForTimeout(3000);

    // Click Next
    await page.getByRole('button', { name: 'Next' }).last().click();
    await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
    await page.waitForTimeout(3000);

    // Get all visible permit/template option texts
    const visiblePermits = await getTemplateOptions(page);

    // Normalize permit names for comparison
    const normalizePermit = (permit: string): string => {
      return permit.toLowerCase().trim().replace(/\s+/g, ' ');
    };

    const expectedPermitsNormalized = testData.expectedPermits.map(normalizePermit);
    const visiblePermitsNormalized = visiblePermits.map(normalizePermit);

    // Check for missing permits
    const missingPermits: string[] = [];
    for (const expected of expectedPermitsNormalized) {
      const found = visiblePermitsNormalized.some(visible => 
        visible.includes(expected) || expected.includes(visible)
      );
      if (!found) {
        missingPermits.push(expected);
      }
    }

    // Check for unexpected permits
    const unexpectedPermits: string[] = [];
    for (const visible of visiblePermitsNormalized) {
      const found = expectedPermitsNormalized.some(expected =>
        visible.includes(expected) || expected.includes(visible)
      );
      if (!found && visible.length > 3) {
        unexpectedPermits.push(visible);
      }
    }

    // Log results
    console.log(`\n=== License ${testData.code} (${testData.number}) ===`);
    console.log(`Expected permits: ${testData.expectedPermits.join(', ')}`);
    console.log(`Visible permits: ${visiblePermits.join(', ')}`);

    if (missingPermits.length > 0) {
      console.log(`❌ Missing permits: ${missingPermits.join(', ')}`);
    }
    if (unexpectedPermits.length > 0) {
      console.log(`❌ Unexpected permits: ${unexpectedPermits.join(', ')}`);
    }

    // Assert no missing or unexpected permits
    expect(missingPermits.length, `Missing permits: ${missingPermits.join(', ')}`).toBe(0);
    expect(unexpectedPermits.length, `Unexpected permits: ${unexpectedPermits.join(', ')}`).toBe(0);
  });
}