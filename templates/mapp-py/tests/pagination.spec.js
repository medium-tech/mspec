import { test } from './fixtures.js';
import { expect } from '@playwright/test';

test('pagination root returns 200', async ({ browser, paginationEnv, paginationSession }) => {
  const context = await browser.newContext({ storageState: paginationSession.storageState });
  const page = await context.newPage();
  
  const response = await page.goto(paginationEnv.host);
  expect(response.status()).toBe(200);
});