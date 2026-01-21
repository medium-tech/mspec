import { test } from './fixtures.js';
import { expect } from '@playwright/test';

test('crud root returns 200', async ({ browser, crudEnv, crudSession }) => {
  const context = await browser.newContext({ storageState: crudSession.storageState });
  const page = await context.newPage();
  
  const response = await page.goto(crudEnv.host);
  expect(response.status()).toBe(200);
});
