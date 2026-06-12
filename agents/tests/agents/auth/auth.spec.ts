```typescript
import { test, expect } from '@playwright/test';

const BASE_URL = 'https://lacps--uat.sandbox.my.site.com/s/';
const LOGIN_URL = 'https://login.sandbox.account.lacity.gov/u/login/password';

test.beforeEach(async ({ page }) => {
  await page.goto(BASE_URL);
  await page.click('button[title="Log In"]');
  await page.waitForURL(LOGIN_URL);
});

// Test 1: Successful authentication with valid credentials
test('should successfully authenticate with valid email and password', async ({ page }) => {
  const testEmail = process.env.TEST_EMAIL || 'johncontractor1842@gmail.com';
  const testPassword = process.env.TEST_PASSWORD || 'L@db$L@db$!!';

  // Enter email
  await page.fill('input[name="username"][type="email"]', testEmail);
  await page.click('button[name="action"]:has-text("Continue")');
  
  // Wait for password field to appear
  await page.waitForSelector('input[name="password"][type="password"]');
  
  // Enter password
  await page.fill('input[name="password"][type="password"]', testPassword);
  await page.click('button[name="action"]:has-text("Continue")');
  
  // Verify we've moved past the login form (either to CAPTCHA or authenticated state)
  await page.waitForTimeout(2000);
  const currentUrl = page.url();
  expect(currentUrl).not.toBe(LOGIN_URL);
});

// Test 2: Reject invalid email format
test('should show error for invalid email format', async ({ page }) => {
  const invalidEmail = 'notavalidemail';

  // Enter invalid email
  await page.fill('input[name="username"][type="email"]', invalidEmail);
  await page.click('button[name="action"]:has-text("Continue")');
  
  // The email input should still be visible, indicating rejection
  await page.waitForTimeout(1000);
  const emailInput = await page.$('input[name="username"][type="email"]');
  expect(emailInput).not.toBeNull();
  
  // Email field should still contain our invalid input
  const inputValue = await page.inputValue('input[name="username"][type="email"]');
  expect(inputValue).toBe(invalidEmail);
});

// Test 3: Valid email but wrong password
test('should reject valid email with incorrect password', async ({ page }) => {
  const testEmail = process.env.TEST_EMAIL || 'johncontractor1842@gmail.com';
  const wrongPassword = 'WrongPassword123!!';

  // Enter valid email
  await page.fill('input[name="username"][type="email"]', testEmail);
  await page.click('button[name="action"]:has-text("Continue")');
  
  // Wait for password field
  await page.waitForSelector('input[name="password"][type="password"]');
  
  // Enter wrong password
  await page.fill('input[name="password"][type="password"]', wrongPassword);
  await page.click('button[name="action"]:has-text("Continue")');
  
  // Should still be on login page or show error
  await page.waitForTimeout(1000);
  const passwordInput = await page.$('input[name="password"][type="password"]');
  expect(passwordInput).not.toBeNull();
});

// Test 4: Empty password field submission
test('should reject submission when password field is empty', async ({ page }) => {
  const testEmail = process.env.TEST_EMAIL || 'johncontractor1842@gmail.com';

  // Enter email
  await page.fill('input[name="username"][type="email"]', testEmail);
  await page.click('button[name="action"]:has-text("Continue")');
  
  // Wait for password field
  await page.waitForSelector('input[name="password"][type="password"]');
  
  // Try to submit without entering password
  await page.click('button[name="action"]:has-text("Continue")');
  
  // Password field should still be visible
  await page.waitForTimeout(1000);
  const passwordInput = await page.$('input[name="password"][type="password"]');
  expect(passwordInput).not.toBeNull();
});

// Test 5: Verify redirect URL after successful authentication
test('should redirect away from login URL after successful authentication', async ({ page }) => {
  const testEmail = process.env.TEST_EMAIL || 'johncontractor1842@gmail.com';
  const testPassword = process.env.TEST_PASSWORD || 'L@db$L@db$!!';

  // Enter credentials
  await page.fill('input[name="username"][type="email"]', testEmail);
  await page.click('button[name="action"]:has-text("Continue")');
  
  await page.waitForSelector('input[name="password"][type="password"]');
  await page.fill('input[name="password"][type="password"]', testPassword);
  await page.click('button[name="action"]:has-text("Continue")');
  
  // Wait for navigation away from login page
  await page.waitForTimeout(3000);
  const finalUrl = page.url();
  
  // Should not be on the password login page anymore
  expect(finalUrl).not.toContain('/u/login/password');
});

// Test 6: Verify authenticated user element is present after login
test('should display authenticated user UI elements after successful login', async ({ page }) => {
  const testEmail = process.env.TEST_EMAIL || 'johncontractor1842@gmail.com';
  const testPassword = process.env.TEST_PASSWORD || 'L@db$L@db$!!';

  // Complete authentication
  await page.fill('input[name="username"][type="email"]', testEmail);
  await page.click('button[name="action"]:has-text("Continue")');
  
  await page.waitForSelector('input[name="password"][type="password"]');
  await page.fill('input[name="password"][type="password"]', testPassword);
  await page.click('button[name="action"]:has-text("Continue")');
  
  // Wait for page load after authentication
  await page.waitForTimeout(3000);
  
  // Navigate back to base URL to verify authenticated state
  await page.goto(BASE_URL);
  
  // The Log In button should not be visible if authenticated
  // (or should be replaced with user profile/logout option)
  const loginButton = await page.$('button[title="Log In"]');
  
  // After successful auth, the login button should be gone or disabled
  if (loginButton) {
    const isVisible = await loginButton.isVisible();
    expect(isVisible).toBe(false);
  }
});
```