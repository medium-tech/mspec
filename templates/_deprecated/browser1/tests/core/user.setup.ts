import { test as setup, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const authFile = path.join(__dirname, '../.auth/user.json');

setup('create and authenticate user', async ({ page }) => {

    const testEmail = `test${Date.now()}@example.com`;
    const testPassword = 'testpassword123';
    const testName = 'Test User';
    
    // Step 1: Create User
    await page.goto('http://localhost:5005/');
    await page.getByRole('button', { name: 'Create User' }).click();
    
    await expect(page.locator('h1')).toContainText('Create User - template_app');
    
    // Fill out the create user form
    await page.locator('input[name="name"]').fill(testName);
    await page.locator('input[name="email"]').fill(testEmail);
    await page.locator('input[name="password1"]').fill(testPassword);
    await page.locator('input[name="password2"]').fill(testPassword);
    
    // Submit the form
    await page.getByRole('button', { name: 'Create User' }).click();
    
    // Wait for success message
    await expect(page.locator('#message')).toContainText('User created successfully');
    
    // Step 2: Login
    await page.getByRole('link', { name: 'Login' }).click();
    
    await expect(page.locator('h1')).toContainText('Login - template_app');
    
    // Fill out the login form
    await page.locator('input[name="email"]').fill(testEmail);
    await page.locator('input[name="password"]').fill(testPassword);
    
    // Submit the login form
    await page.getByRole('button', { name: 'Login' }).click();
    
    // Wait for success message and redirect
    await expect(page.locator('#message')).toContainText('Login successful');
    
    // Wait for redirect to home page
    await page.waitForURL('http://localhost:5005/');

    // Store state for future tests
    await page.context().storageState({ path: authFile });

});