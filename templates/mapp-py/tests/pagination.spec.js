import { test } from './fixtures.js';
import { expect } from '@playwright/test';

test('pagination root returns 200', async ({ page, paginationEnv }) => {
  const { host: paginationHost } = paginationEnv;
  const response = await page.goto(paginationHost);
  expect(response.status()).toBe(200);
});
