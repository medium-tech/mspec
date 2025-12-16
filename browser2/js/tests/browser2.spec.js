import { test, expect } from '@playwright/test';

test('test - hello world', async ({ page }) => {
  await page.goto('http://localhost:8000/');
  await expect(page.locator('h1')).toContainText('Hello World');
  await expect(page.locator('span')).toContainText('I am a sample page.');
  await expect(page.locator('#debug-content')).toContainText('Lingo: page-beta-1');
});


test('test - test page', async ({ page }) => {
  await page.goto('http://localhost:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/test-page.json');

  await expect(page.locator('h1')).toContainText('Example document');
  await expect(page.locator('#lingo-app')).toContainText('Please tell us your name:');
  await expect(page.locator('input[type="text"]')).toBeVisible();
  await expect(page.locator('#lingo-app')).toContainText('Here\'s a random number: 0. It\'s small.');
  await expect(page.getByRole('button', { name: 'Randomize' })).toBeVisible();
  await expect(page.locator('#lingo-app')).toContainText('Randomize');
  await expect(page.locator('#lingo-app')).toContainText('Welcome back, Unknown person!');
  await page.locator('#lingo-app-params-textarea').fill('{\n    "first_visit": true\n}');

  await page.getByRole('button', { name: 'Run' }).click();
  await expect(page.locator('#lingo-app')).toContainText('Welcome in, Unknown person!');
  await page.locator('input[type="text"]').click();
  await page.locator('input[type="text"]').fill('Alice');
  await expect(page.locator('#lingo-app')).toContainText('Welcome in, Alice!');

  await page.getByRole('button', { name: 'Randomize' }).click();
  // the random number will be 1 <= x <= 100, so just check that it's not the initial value of 0
  await expect(page.locator('#lingo-app')).not.toContainText('Here\'s a random number: 0. It\'s small.');
  await expect(page.locator('#lingo-app')).toContainText('Here\'s a random number:');
});