import { test, expect } from '@playwright/test';
import { resolve } from 'path';
import { readFileSync } from 'fs';

// Helper function to parse env file
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

// Load crud environment variables
const crudEnvPath = resolve(process.cwd(), 'mapp-tests/crud.env');
const crudEnv = parseEnvFile(crudEnvPath);
const crudHost = crudEnv.MAPP_CLIENT_HOST;
expect(crudHost).toBeDefined();
expect(crudHost).toMatch(/^http:\/\/localhost:\d+$/);

// Make request to /api/spec with fetch api
const crudResp = await fetch(`${crudHost}/api/spec`);
expect(crudResp.ok).toBeTruthy();
expect(crudResp.status).toBe(200);

// Verify spec structure
const crudSpec = await crudResp.json();
expect(crudSpec).toBeDefined();
expect(crudSpec.project).toBeDefined();
expect(crudSpec.modules).toBeDefined();

// Load pagination environment variables
const paginationEnvPath = resolve(process.cwd(), 'mapp-tests/pagination.env');
const paginationEnv = parseEnvFile(paginationEnvPath);
const paginationHost = paginationEnv.MAPP_CLIENT_HOST;
expect(paginationHost).toBeDefined();
expect(paginationHost).toMatch(/^http:\/\/localhost:\d+$/);

// Make request to /api/spec with fetch api
const paginationResp = await fetch(`${paginationHost}/api/spec`);
expect(paginationResp.ok).toBeTruthy();
expect(paginationResp.status).toBe(200);

// Verify spec structure
const paginationSpec = await paginationResp.json();
expect(paginationSpec).toBeDefined();
expect(paginationSpec.project).toBeDefined();
expect(paginationSpec.modules).toBeDefined();

// veridy crudSpec and paginationSpec are equal
expect(crudSpec).toEqual(paginationSpec);

const appSpec = crudSpec;

test.describe('MAPP Spec Loading', () => {
  
  test('should load spec from crud environment', async ({ request }) => {
    
    // Make request to /api/spec
    const response = await request.get(`${crudHost}/api/spec`);
    
    // Verify response
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    // Verify spec structure
    const spec = await response.json();
    expect(spec).toBeDefined();
    expect(spec.project).toBeDefined();
    expect(spec.modules).toBeDefined();
  });

  test('should load spec from pagination environment', async ({ request }) => {

    expect(paginationHost).toMatch(/^http:\/\/localhost:\d+$/);
    
    // Make request to /api/spec
    const response = await request.get(`${paginationHost}/api/spec`);
    
    // Verify response
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    // Verify spec structure
    const spec = await response.json();
    expect(spec).toBeDefined();
    expect(spec.project).toBeDefined();
    expect(spec.modules).toBeDefined();
  });
  
});

test('test user auth flow', async ({ page }) => {

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
  await page.getByRole('row', { name: 'Email: Email of the user' }).getByRole('textbox').fill('test@email.com');
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
  await page.locator('input[type="text"]').fill('test@email.com');
  await page.locator('input[type="password"]').click();
  await page.locator('input[type="password"]').fill('123');
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('success:');

  // get current user //

  await page.getByRole('link', { name: 'auth' }).click();
  await page.getByRole('link', { name: 'current-user' }).click();
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('tbody')).toContainText('test@email.com');

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
  await page.locator('input[type="text"]').fill('test@email.com');
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