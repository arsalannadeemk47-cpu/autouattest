import { test, expect } from '@playwright/test';

test('user can log in and is redirected to homepage with Guided Help', async ({ page }) => {
  await page.goto('https://lacps--uat.sandbox.my.site.com/s/');

  // Click the login button on the landing page
  const loginButton = page.locator(
    'a:has-text("Log In"), a:has-text("Login"), button:has-text("Log In"), button:has-text("Login")'
  ).first();
  await expect(loginButton).toBeVisible({ timeout: 15000 });
  await loginButton.click();

  // Wait for the login form to render
  const usernameInput = page.locator('#username, input[type="email"], input[name*="email"], input[id*="email"]').first();
  const passwordInput = page.locator('#password, input[type="password"], input[name*="password"], input[id*="password"]').first();
  await expect(usernameInput).toBeVisible({ timeout: 15000 });
  await expect(passwordInput).toBeVisible({ timeout: 15000 });

  await usernameInput.fill('johncontractor1842@gmail.com');
  await passwordInput.fill('L@db$L@db$!!');

  const submitButton = page.locator(
    '#Login, input[type="submit"], button:has-text("Log In"), button:has-text("Login"), button:has-text("Sign In")'
  ).first();
  await expect(submitButton).toBeVisible({ timeout: 10000 });
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }),
    submitButton.click(),
  ]);

  // Confirm landing on the home page
  await expect(page).toHaveURL(/home|dashboard|welcome|s\//i);
  await expect(page.locator('button:has-text("Guided Help"), text=Guided Help')).toBeVisible({ timeout: 15000 });
});
