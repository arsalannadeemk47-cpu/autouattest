const { test, expect } = require('@playwright/test');

test('clicking login button redirects to login page', async ({ page }) => {
  await page.goto('https://lacps--uat.sandbox.my.site.com/s/');

  // Find a visible Login / Log In button or link (covers common label variations)
  const loginButton = page.locator(
    'a:has-text("Log In"), a:has-text("Login"), button:has-text("Log In"), button:has-text("Login")'
  ).first();

  await expect(loginButton).toBeVisible({ timeout: 10000 });
  await loginButton.click();

  // Wait for navigation to finish and assert the URL shows a login page
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveURL(/login/i);
});
