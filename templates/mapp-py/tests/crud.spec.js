import { test } from './fixtures.js';
import { expect } from '@playwright/test';

test('crud root returns 200', async ({ page, crudEnv }) => {
  const { host: crudHost } = crudEnv;
  const response = await page.goto(crudHost);
  expect(response.status()).toBe(200);
});
