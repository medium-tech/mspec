import { test as base, expect } from '@playwright/test';
import { getEnvSpec } from './env-helpers.js';

async function createAndLoginUser(host, browser, envName) {
  const uniqueId = Date.now();
  const email = `${envName}-user-${uniqueId}@example.com`;
  const password = 'pw' + uniqueId;

  // Create user via UI
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(host);
  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'create-user' }).click();
  await page.getByRole('row', { name: /Name:/ }).getByRole('textbox').fill('Test User');
  await page.getByRole('row', { name: /Email:/ }).getByRole('textbox').fill(email);
  await page.getByRole('row', { name: /Password:/ }).getByRole('textbox').fill(password);
  await page.getByRole('row', { name: /Password confirm:/ }).getByRole('textbox').fill(password);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.waitForSelector('#lingo-app');

  // Login user via UI
  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'login-user' }).click();
  await page.locator('input[type="text"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.waitForSelector('#lingo-app');

  // Save storage state
  const storageState = await context.storageState();
  await context.close();
  return { email, password, storageState };
}

export const test = base.extend({
  crudEnv: [
    async ({}, use) => {
      const { host, spec } = await getEnvSpec('mapp-tests/crud.env', expect);
      await use({ host, spec });
    },
    { scope: 'worker' }
  ],
  paginationEnv: [
    async ({}, use) => {
      const { host, spec } = await getEnvSpec('mapp-tests/pagination.env', expect);
      await use({ host, spec });
    },
    { scope: 'worker' }
  ],
  crudSession: [
    async ({ browser, crudEnv }, use) => {
      const { host } = crudEnv;
      const session = await createAndLoginUser(host, browser, 'crud');
      await use(session);
    },
    { scope: 'worker' }
  ],
  paginationSession: [
    async ({ browser, paginationEnv }, use) => {
      const { host } = paginationEnv;
      const session = await createAndLoginUser(host, browser, 'pagination');
      await use(session);
    },
    { scope: 'worker' }
  ]
});
