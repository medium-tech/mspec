import { test, expect } from '@playwright/test';

// vars :: {"template_app":"project.name.snake_case", "http://localhost:5005": "client.default_host"}

test.describe('Authentication Workflow', () => {
  
  test.beforeEach(async ({ page }) => {
    // Clear any existing session data before each test
    await page.goto('http://localhost:5005/');
    await page.evaluate(() => {
      localStorage.clear();
    });
  });

  test('should display correct buttons when logged out', async ({ page }) => {
    await page.goto('http://localhost:5005/');
    
    // Check that logged out buttons are visible
    await expect(page.locator('#loggedOutButtons')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create User' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
    
    // Check that logged in buttons are hidden
    await expect(page.locator('#loggedInButtons')).toBeHidden();
  });

  test('should complete full user workflow: create user, login, logout', async ({ page }) => {
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
    
    // Step 3: Verify logged in state
    await expect(page.locator('#loggedOutButtons')).toBeHidden();
    await expect(page.locator('#loggedInButtons')).toBeVisible();
    await expect(page.locator('#welcomeMessage')).toContainText(`Welcome, ${testEmail}!`);
    await expect(page.getByRole('button', { name: 'User Account' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
    
    // Step 4: Test User Account page
    await page.getByRole('button', { name: 'User Account' }).click();
    await expect(page.locator('h1')).toContainText('User Account - template_app');
    await expect(page.locator('#userEmail')).toContainText(testEmail);
    
    // Go back to home page
    await page.getByRole('link', { name: 'Home' }).click();
    
    // Step 5: Logout
    await page.getByRole('button', { name: 'Logout' }).click();
    
    // Verify logged out state
    await expect(page.locator('#loggedOutButtons')).toBeVisible();
    await expect(page.locator('#loggedInButtons')).toBeHidden();
    await expect(page.getByRole('button', { name: 'Create User' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
    await expect(page.locator('#message')).toContainText('You have been logged out');
  });

  test('should handle login with invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:5005/auth/login.html');
    
    // Try to login with invalid credentials
    await page.locator('input[name="email"]').fill('invalid@example.com');
    await page.locator('input[name="password"]').fill('wrongpassword');
    await page.getByRole('button', { name: 'Login' }).click();
    
    // Should show error message
    await expect(page.locator('#message')).toContainText('Login failed');
    
    // Should still be on login page
    await expect(page.locator('h1')).toContainText('Login - template_app');
  });

  test('should validate password confirmation on create user', async ({ page }) => {
    await page.goto('http://localhost:5005/auth/create-user.html');
    
    // Fill form with mismatched passwords
    await page.locator('input[name="name"]').fill('Test User');
    await page.locator('input[name="email"]').fill('test@example.com');
    await page.locator('input[name="password1"]').fill('password123');
    await page.locator('input[name="password2"]').fill('different123');
    
    // Submit the form
    await page.getByRole('button', { name: 'Create User' }).click();
    
    // Should show error message for password mismatch
    await expect(page.locator('#message')).toContainText('Passwords do not match');
  });

  test('should persist login state after page refresh', async ({ page }) => {
    const testEmail = `persistent${Date.now()}@example.com`;
    const testPassword = 'testpassword123';
    
    // Create and login user first
    await page.goto('http://localhost:5005/auth/create-user.html');
    await page.locator('input[name="name"]').fill('Persistent User');
    await page.locator('input[name="email"]').fill(testEmail);
    await page.locator('input[name="password1"]').fill(testPassword);
    await page.locator('input[name="password2"]').fill(testPassword);
    await page.getByRole('button', { name: 'Create User' }).click();
    await expect(page.locator('#message')).toContainText('User created successfully');
    
    // Login
    await page.goto('http://localhost:5005/auth/login.html');
    await page.locator('input[name="email"]').fill(testEmail);
    await page.locator('input[name="password"]').fill(testPassword);
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL('http://localhost:5005/');
    
    // Verify logged in state
    await expect(page.locator('#loggedInButtons')).toBeVisible();
    
    // Refresh the page
    await page.reload();
    
    // Should still be logged in after refresh
    await expect(page.locator('#loggedInButtons')).toBeVisible();
    await expect(page.locator('#loggedOutButtons')).toBeHidden();
    await expect(page.locator('#welcomeMessage')).toContainText(`Welcome, ${testEmail}!`);
  });

});