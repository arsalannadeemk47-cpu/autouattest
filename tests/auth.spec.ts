import { test, expect } from '@playwright/test';

const BASE_URL = 'https://lacps--uat.sandbox.my.site.com/s/';
const LOGIN_URL = 'https://login.sandbox.account.lacity.gov/u/login/password';

// Helper to submit a form step — clicks the visible, non-hidden action button
async function clickContinue(page) {
  await page.locator('button[name="action"]:not([aria-hidden="true"])').click();
}

test.beforeEach(async ({ page }) => {
  // Session already authenticated via saved state
  // Just navigate directly to the app
  await page.goto('https://lacps--uat.sandbox.my.site.com/s/');
});

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.locator('button[title="Log In"]').click();
    // Wait for login page to fully load
    await page.waitForURL('**/login**');
  });

  // Test Case 1: Successful authentication with valid credentials
  test('should successfully authenticate with valid email and password', async ({ page }) => {
    const testEmail = process.env.TEST_EMAIL;
    const testPassword = process.env.TEST_PASSWORD;

    // Fill email and submit
    await page.locator('input[name="username"]').fill(testEmail);
    await clickContinue(page);

    // Wait for password field to appear
    await page.waitForSelector('input[name="password"]', { timeout: 10000 });
    await page.locator('input[name="password"]').fill(testPassword);
    await clickContinue(page);

    // Wait for redirect away from login
    await page.waitForURL(url => !url.toString().includes('login'), { timeout: 30000 });

    const currentUrl = page.url();
    expect(currentUrl).not.toContain('login');
  });

  // Test Case 2: Invalid email format rejection
  test('should reject invalid email format', async ({ page }) => {
    await page.locator('input[name="username"]').fill('invalidemail');
    await clickContinue(page);

    // Form should not progress — email field still visible
    await expect(page.locator('input[name="username"]')).toBeVisible();
    expect(page.url()).toContain('login');
  });

  // Test Case 3: Valid email but wrong password
  test('should reject valid email with incorrect password', async ({ page }) => {
    await page.locator('input[name="username"]').fill(process.env.TEST_EMAIL);
    await clickContinue(page);

    await page.waitForSelector('input[name="password"]', { timeout: 10000 });
    await page.locator('input[name="password"]').fill('WrongPassword123!!');
    await clickContinue(page);

    // Should stay on login page with error
    await page.waitForTimeout(3000);
    await expect(page.locator('input[name="password"]')).toBeVisible();
    expect(page.url()).toContain('login');
  });

  // Test Case 4: Empty email field submission
  test('should not allow submission with empty email field', async ({ page }) => {
    // Attempt to submit without filling email
    await clickContinue(page);

    // Email field should still be visible and we stay on login
    await expect(page.locator('input[name="username"]')).toBeVisible();
    expect(page.url()).toContain('login');
  });

  // Test Case 5: Empty password field submission
  test('should not allow submission with empty password field', async ({ page }) => {
    await page.locator('input[name="username"]').fill(process.env.TEST_EMAIL);
    await clickContinue(page);

    await page.waitForSelector('input[name="password"]', { timeout: 10000 });

    // Attempt to submit without filling password
    await clickContinue(page);

    // Should stay on password step
    await expect(page.locator('input[name="password"]')).toBeVisible();
    expect(page.url()).toContain('login');
  });

  // Test Case 6: Verify redirect URL after successful authentication
  test('should redirect away from login after successful auth', async ({ page }) => {
    await page.locator('input[name="username"]').fill(process.env.TEST_EMAIL);
    await clickContinue(page);

    await page.waitForSelector('input[name="password"]', { timeout: 10000 });
    await page.locator('input[name="password"]').fill(process.env.TEST_PASSWORD);
    await clickContinue(page);

    await page.waitForURL(url => !url.toString().includes('login'), { timeout: 30000 });

    const finalUrl = page.url();
    expect(finalUrl).not.toContain('login.sandbox.account.lacity.gov');
    expect(finalUrl).not.toContain('/u/login/');
  });

  // Test Case 7: Verify authenticated element visible after login
  test('should hide login button after successful authentication', async ({ page }) => {
    await page.locator('input[name="username"]').fill(process.env.TEST_EMAIL);
    await clickContinue(page);

    await page.waitForSelector('input[name="password"]', { timeout: 10000 });
    await page.locator('input[name="password"]').fill(process.env.TEST_PASSWORD);
    await clickContinue(page);

    await page.waitForURL(url => !url.toString().includes('login'), { timeout: 30000 });

    // Login button should no longer be visible on authenticated page
    await expect(page.locator('button[title="Log In"]')).not.toBeVisible();
  });
});