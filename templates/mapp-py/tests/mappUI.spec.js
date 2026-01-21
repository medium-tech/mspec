import { test, expect } from '@playwright/test';
import { resolve } from 'path';
import { readFileSync } from 'fs';

//
// env helpers
//

function parseEnvFile(filePath) {
  try {
    const envContent = readFileSync(filePath, 'utf-8');
    const env = {};
    envContent.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          let value = valueParts.join('=');
          // Remove quotes if present
          value = value.replace(/^["']|["']$/g, '');
          env[key] = value;
        }
      }
    });
    return env;
  } catch (error) {
    throw new Error(`Failed to read env file ${filePath}: ${error.message}`);
  }
}

async function getEnvSpec(envFileName) {

  // Load crud environment variables
  const path = resolve(process.cwd(), envFileName);
  const env = parseEnvFile(path);
  const host = env.MAPP_CLIENT_HOST;
  expect(host).toBeDefined();
  expect(host).toMatch(/^http:\/\/localhost:\d+$/);

  // Make request to /api/spec with fetch api
  const response = await fetch(`${host}/api/spec`);
  expect(response.ok).toBeTruthy();
  expect(response.status).toBe(200);

  // Verify spec structure
  const spec = await response.json();
  expect(spec).toBeDefined();
  expect(spec.project).toBeDefined();
  expect(spec.modules).toBeDefined();

  return { host: host, spec: spec };
}

//
// initialize test env
//

const { host: crudHost, spec: crudSpec } = await getEnvSpec('mapp-tests/crud.env');
const { host: paginationHost, spec: paginationSpec } = await getEnvSpec('mapp-tests/pagination.env');
expect(crudSpec).toEqual(paginationSpec);
const appSpec = crudSpec;

//
// tests
//

test('test user auth flow', async ({ page }) => {

  const uniqueId = Date.now();
  const uniqueEmail = `test-auth-flow-${uniqueId}@email.com`;

  // init //

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