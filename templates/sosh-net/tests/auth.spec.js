import { test } from './fixtures.js';
import { expect } from '@playwright/test';

//
// tests
//

test('test user auth flow', async ({ browser, crudEnv }) => {

  const { host: crudHost } = crudEnv;
  const uniqueId = Date.now();
  const uniqueEmail = `test-auth-flow-${uniqueId}@email.com`;

  // init //
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(crudHost);
  await context.addCookies([{ 
    name: 'protocol_mode', 
    value: 'true', 
    path: '/',
    domain: new URL(crudHost).hostname,
    secure: false,
  }]);
  await page.reload();
  await page.goto(crudHost);
  await page.getByRole('link', { name: 'auth' }).click();
  await expect(page.locator('h1')).toContainText(':: auth');
  await expect(page.locator('#lingo-app')).toContainText(':: available models');
  await expect(page.locator('#lingo-app')).toContainText(':: available operations');

  // create user //
  
  await page.getByRole('link', { name: 'create-user' }).click();
  await page.getByRole('row', { name: 'Name: Name of the user' }).getByRole('textbox').click();
  await page.getByRole('row', { name: 'Name: Name of the user' }).getByRole('textbox').fill('Test User');
  await page.getByRole('row', { name: 'Email: Email of the user' }).getByRole('textbox').click();
  await page.getByRole('row', { name: 'Email: Email of the user' }).getByRole('textbox').fill(uniqueEmail);
  await page.getByRole('row', { name: 'Password: Password for the' }).getByRole('textbox').click();
  await page.getByRole('row', { name: 'Password: Password for the' }).getByRole('textbox').fill('123');
  await page.getByRole('row', { name: 'Password confirm: Password' }).getByRole('textbox').click();
  await page.getByRole('row', { name: 'Password confirm: Password' }).getByRole('textbox').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success:');

  // login //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'login-user' }).click();
  await page.locator('input[type="text"]').click();
  await page.locator('input[type="text"]').fill(uniqueEmail);
  await page.locator('input[type="password"]').click();
  await page.locator('input[type="password"]').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success:');

  // get current user //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'current-user' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('tbody')).toContainText(uniqueEmail);

  // logout current session //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'logout-user' }).click();
  await page.getByRole('combobox').selectOption('current');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success:');

  // confirm cannot get current user //
  
  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'current-user' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('error:');
  await expect(page.locator('#lingo-app')).toContainText('Not logged in');

  // login again //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'login-user' }).click();
  await page.locator('input[type="text"]').click();
  await page.locator('input[type="text"]').fill(uniqueEmail);
  await page.locator('input[type="password"]').click();
  await page.locator('input[type="password"]').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success:');

  // delete user //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'delete-user' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success:');
  await expect(page.locator('tbody')).toContainText('User deleted successfully');

  // confirm cannot get current user //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'current-user' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('error:');
  
});