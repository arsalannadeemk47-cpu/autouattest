import { test } from '@playwright/test';

const BASE_URL = 'https://lacps--uat.sandbox.my.site.com/s/';
const PERMIT_SEARCH_URL = 'https://lacps--uat.sandbox.my.site.com/s/permit-search';
const STREET_NUMBER = '201';
const STREET_NAME = 'Figueroa';
const TEST_PERMIT_NUMBER = '20041-90000-19160';

test('DEBUG - inspect dialog after clicking permit', async ({ page }) => {
  await page.goto(BASE_URL);

  const closeButton = page.getByRole('button', { name: /close/i }).first();
  if (await closeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await closeButton.click();
  }

  await page.getByRole('button', { name: /^permits$/i }).click();
  await page.getByRole('link', { name: /permit search/i }).click();
  await page.waitForURL(`**${PERMIT_SEARCH_URL}**`, { timeout: 10000 });
  await page.waitForTimeout(2000);

  await page.getByLabel(/street number/i).fill(STREET_NUMBER);
  await page.getByLabel(/street name/i).fill(STREET_NAME);
  await page.getByRole('button', { name: /^search$/i }).click();
  await page.waitForTimeout(4000);

  const permitLink = page.getByRole('link', { name: TEST_PERMIT_NUMBER })
    .or(page.getByRole('button', { name: TEST_PERMIT_NUMBER }))
    .first();
  await permitLink.click();
  await page.waitForTimeout(3000);

  // Log each dialog's visibility and a snippet of its HTML
  const dialogs = page.locator('[role="dialog"]');
  const count = await dialogs.count();
  console.log(`Found ${count} dialogs`);

  for (let i = 0; i < count; i++) {
    const dialog = dialogs.nth(i);
    const visible = await dialog.isVisible().catch(() => false);
    const html = await dialog.innerHTML().catch(() => 'error');
    console.log(`\nDialog ${i}: visible=${visible}`);
    console.log(`HTML snippet: ${html.slice(0, 500)}`);
  }

  // Also log the modal with the permit number in it
  const permitInPage = page.getByText(TEST_PERMIT_NUMBER, { exact: true });
  const allMatches = await permitInPage.count();
  console.log(`\nPermit number appears ${allMatches} times on page`);

  for (let i = 0; i < allMatches; i++) {
    const match = permitInPage.nth(i);
    const visible = await match.isVisible().catch(() => false);
    const parent = match.locator('..');
    const grandparent = parent.locator('..');
    const greatGrandparent = grandparent.locator('..');
    console.log(`\nMatch ${i}: visible=${visible}`);
    console.log(`Grandparent tag/class: ${await grandparent.evaluate(el => el.tagName + ' ' + el.className).catch(() => 'error')}`);
    console.log(`Great-grandparent tag/class: ${await greatGrandparent.evaluate(el => el.tagName + ' ' + el.className).catch(() => 'error')}`);
  }
});