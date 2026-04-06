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

  // confirm is not logged in //

  await page.getByRole('link', { name: 'is-logged-in' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('false');

  // create user //
  
  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'create-user' }).click();
  await page.getByRole('row', { name: 'Name: Name of the user' }).getByRole('textbox').fill('Test User');
  await page.getByRole('row', { name: 'Email: Email of the user' }).getByRole('textbox').fill(uniqueEmail);
  await page.getByRole('row', { name: 'Password: show' }).getByRole('textbox').fill('123');
  await page.getByRole('row', { name: 'Password confirm: show' }).getByRole('textbox').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success');

  // login //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'login-user' }).click();
  await page.locator('input[type="text"]').click();
  await page.locator('input[type="text"]').fill(uniqueEmail);
  await page.locator('input[type="password"]').click();
  await page.locator('input[type="password"]').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success');

  // get current user //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'current-user' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('tbody')).toContainText(uniqueEmail);

  // confirm is logged in //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'is-logged-in' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('true');

  // logout current session //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'logout-user' }).click();
  await page.getByRole('combobox').selectOption('current');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success');

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
  await expect(page.locator('#lingo-app')).toContainText('success');

  // delete user //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'delete-user' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success');
  await expect(page.locator('tbody')).toContainText('User deleted successfully');

  // confirm cannot get current user //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'current-user' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('error:');
  
});

test('test redacted fields', async ({ page }) => {

  // test that sensitive fields in forms and responses are redacted appropriately
  
  await page.goto('http://localhost:3003/');
  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'create-user' }).click();

  //
  // create user
  //

  const curDate = new Date().getTime();
  const uniqueEmail = `afakeemail+${curDate}@email.com`;

  await expect(page.locator('input[type="password"]')).toHaveCount(2);

  await page.getByRole('row', { name: 'name: Name of the user' }).getByRole('textbox').fill('test user redacted fields');
  await page.getByRole('row', { name: 'email: Email of the user' }).getByRole('textbox').fill(uniqueEmail);
  await page.getByRole('row', { name: 'password: show' }).getByRole('textbox').fill('123');
  await page.getByRole('row', { name: 'password confirm: show' }).getByRole('textbox').fill('123');

  // click show password buttons
  await page.getByRole('button', { name: 'show' }).first().click();
  await page.getByRole('button', { name: 'show' }).first().click();

  // ensure no password fields are visible (they changed to text type)
  await expect(page.locator('input[type="password"]')).toHaveCount(0);
  
  // click hide password buttons
  await page.getByRole('button', { name: 'hide' }).first().click();
  await page.getByRole('button', { name: 'hide' }).first().click();

  // ensure password fields are back to type password
  await expect(page.locator('input[type="password"]')).toHaveCount(2);

  // create user
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success');

  //
  // login user
  //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'login-user' }).click();
  await expect(page.locator('input[type="password"]')).toHaveCount(1);
  
  await page.locator('input[type="text"]').fill(uniqueEmail);
  await page.locator('input[type="password"]').fill('123');
  
  // show/hide password again
  await page.getByRole('button', { name: 'show' }).click();
  await expect(page.locator('input[type="password"]')).toHaveCount(0);
  await page.getByRole('button', { name: 'hide' }).click();
  await expect(page.locator('input[type="password"]')).toHaveCount(1);

  // login and confirm access_token is redacted
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success');
  await expect(page.locator('tbody')).toContainText('access_token');
  await expect(page.locator('tbody')).toContainText('REDACTED');
  
  // show/hide access_token
  await page.getByRole('button', { name: 'show access_token' }).click();
  await expect(page.locator('tbody')).not.toContainText('REDACTED');
  await page.getByRole('button', { name: 'hide access_token' }).click();
  await expect(page.locator('#lingo-app')).toContainText('show access_token');
  await expect(page.locator('tbody')).toContainText('REDACTED');

});