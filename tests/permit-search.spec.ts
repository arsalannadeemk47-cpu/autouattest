import { test, expect } from '@playwright/test';

const BASE_URL = 'https://lacps--uat.sandbox.my.site.com/s/';
const PERMIT_SEARCH_URL = 'https://lacps--uat.sandbox.my.site.com/s/permit-search';
const STREET_NUMBER = '201';
const STREET_NAME = 'Figueroa';
const TEST_PERMIT_NUMBER = '20041-90000-19160';

// Helper: navigate to permit search from homepage
async function goToPermitSearch(page) {
  await page.goto(BASE_URL);

  // Dismiss modal if present
  const closeButton = page.getByRole('button', { name: /close/i }).first();
  if (await closeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await closeButton.click();
  }

  // Open Permits menu then click Permit Search
  await page.getByRole('button', { name: /^permits$/i }).click();
  await page.getByRole('link', { name: /permit search/i }).click();
  await page.waitForURL(`**${PERMIT_SEARCH_URL}**`, { timeout: 10000 });
  await page.waitForTimeout(2000);
}

// Helper: fill address fields and submit search
async function performSearch(page, streetNumber: string, streetName: string) {
  await page.getByLabel(/street number/i).fill(streetNumber);
  await page.getByLabel(/street name/i).fill(streetName);
  await page.getByRole('button', { name: /^search$/i }).click();
  await page.waitForTimeout(4000);
}

test.describe('Permit Search Workflow', () => {

  // Test 1: Permit search is reachable from homepage via Permits menu
  test('NAVIGATION - Permit search is findable from homepage', async ({ page }) => {
    await goToPermitSearch(page);

    await expect(page).toHaveURL(new RegExp(PERMIT_SEARCH_URL));
    await expect(page.getByLabel(/street number/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByLabel(/street name/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /^search$/i })).toBeVisible();
  });

  // Test 2: Searching a valid address returns a results table
  test('SUCCESSFUL SEARCH - Address search returns results', async ({ page }) => {
    await goToPermitSearch(page);
    await performSearch(page, STREET_NUMBER, STREET_NAME);

    // Results table should appear
    await expect(page.getByRole('table').or(
      page.locator('[role="grid"]')
    ).first()).toBeVisible({ timeout: 15000 });

    // More than just the header row should be present
    const rows = page.locator('[role="row"]');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(1);
  });

  // Test 3: Results table contains permit number, date and status columns
  test('RESULTS FORMAT - Results contain correct data fields', async ({ page }) => {
    await goToPermitSearch(page);
    await performSearch(page, STREET_NUMBER, STREET_NAME);

    // Use span[title] since column headers are inside a clipped container
    await expect(
      page.locator('span[title="Permit Number"]').first()
    ).toBeAttached({ timeout: 15000 });

    await expect(
      page.locator('span[title="Date"], span[title="Status Date"], span[title="Issued Date"]').first()
    ).toBeAttached({ timeout: 15000 });

    await expect(
      page.locator('span[title="Phase"]').first()
    ).toBeAttached({ timeout: 15000 });
  });

  // Test 4: Specific permit number appears in results for searched address
  test('SPECIFIC PERMIT - Test permit number appears in results', async ({ page }) => {
    await goToPermitSearch(page);
    await performSearch(page, STREET_NUMBER, STREET_NAME);

    await expect(
      page.getByText(TEST_PERMIT_NUMBER, { exact: true })
    ).toBeVisible({ timeout: 15000 });
  });

 // Test 5: Clicking a permit number opens its detail view
  test('PERMIT DETAIL - Clicking permit opens detail page', async ({ page }) => {
    await goToPermitSearch(page);
    await performSearch(page, STREET_NUMBER, STREET_NAME);

    // Find the permit button in results and click it
    const permitLink = page.getByRole('link', { name: TEST_PERMIT_NUMBER })
      .or(page.getByRole('button', { name: TEST_PERMIT_NUMBER }))
      .first();

    await expect(permitLink).toBeVisible({ timeout: 15000 });
    await permitLink.click();
    await page.waitForTimeout(3000);

    // The detail modal should be visible — it has class slds-modal__container
    const detailModal = page.locator('.slds-modal__container');
    await expect(detailModal).toBeVisible({ timeout: 10000 });

    // The modal header should say "Permit Details"
    await expect(
      detailModal.getByRole('heading', { name: /permit details/i })
    ).toBeVisible({ timeout: 5000 });

    // The permit number should appear inside the slds-box section
    // of the modal, not in the results table button
    await expect(
      detailModal.locator('.slds-box').getByText(TEST_PERMIT_NUMBER, { exact: true })
    ).toBeVisible({ timeout: 10000 });
  });

  // Test 6: Submitting empty search shows validation
  test('EMPTY SEARCH - Submitting empty search shows validation', async ({ page }) => {
    await goToPermitSearch(page);

    await page.getByRole('button', { name: /^search$/i }).click();
    await page.waitForTimeout(2000);

    await expect(
      page.getByText(/No records found\./i)
    ).toBeVisible({ timeout: 5000 });
  });

  // Test 7: Searching a nonsense address shows a no results message
  test('NO RESULTS - Search with invalid address shows no results', async ({ page }) => {
    await goToPermitSearch(page);
    await performSearch(page, 'ZZZZ99999', 'Fake St');

    await expect(
      page.getByText(/No records found\./i)
    ).toBeVisible({ timeout: 15000 });
  });

  // Test 8: Running a second search loads fresh results
  test('SEARCH RESET - Searching again after results loads new results', async ({ page }) => {
    await goToPermitSearch(page);
    await performSearch(page, STREET_NUMBER, STREET_NAME);

    await expect(
      page.getByRole('table').or(page.locator('[role="grid"]')).first()
    ).toBeVisible({ timeout: 15000 });

    // Clear and search with a different address
    await page.getByLabel(/street number/i).clear();
    await page.getByLabel(/street name/i).clear();
    await performSearch(page, '100', 'Main St');

    // Either new results or a no results message should appear
    const outcome = page.getByRole('table').or(page.locator('[role="grid"]')).first()
      .or(page.getByText(/No records found|no permits/i).first());

    await expect(outcome).toBeVisible({ timeout: 15000 });
  });
});