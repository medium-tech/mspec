import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:8000/');
  await expect(page.locator('h1')).toContainText('Hello World');
  await expect(page.locator('span')).toContainText('I am a sample page.');
  await expect(page.locator('#debug-content')).toContainText('Lingo: page-beta-1');
});