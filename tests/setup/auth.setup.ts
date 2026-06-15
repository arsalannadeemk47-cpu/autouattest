import { chromium } from '@playwright/test';
import path from 'path';

async function saveAuthState() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Navigate to site
  await page.goto('https://lacps--uat.sandbox.my.site.com/s/');
  
  console.log('\n===========================================');
  console.log('Please log in manually in the browser window.');
  console.log('The script will wait until you are authenticated.');
  console.log('===========================================\n');

  // Wait until you've manually completed login including CAPTCHA
  await page.waitForURL(
    url => !url.toString().includes('login'),
    { timeout: 120000 } // 2 minutes to log in manually
  );

  console.log('✅ Authenticated! Saving session...');

  // Save the authenticated state
  await context.storageState({ 
    path: path.resolve(process.cwd(), 'tests/setup/.auth/user.json') 
  });

  console.log('✅ Session saved to tests/setup/.auth/user.json');
  await browser.close();
}

saveAuthState();