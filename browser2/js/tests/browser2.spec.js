import { test, expect } from '@playwright/test';

test('test - hello world', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await expect(page.locator('h1')).toContainText('Hello World');
  await expect(page.locator('span')).toContainText('I am a sample page.');
  await expect(page.locator('#debug-content')).toContainText('Lingo: page-beta-1');
});


test('test - test page', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
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

test('test - hello_world script', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  
  // Load test data
  const response = await page.request.get('http://127.0.0.1:8000/data/lingo/scripts/hello_world_test_data.json');
  const testData = await response.json();
  
  // Test with default params
  await page.locator('#spec-select').selectOption('data/lingo/scripts/hello_world.json');
  await expect(page.locator('#lingo-app')).toContainText(`"value": ${testData.results.default.value}`);
  await expect(page.locator('#lingo-app')).toContainText(`"type": "${testData.results.default.type}"`);
  
  // Test each test case
  for (const testCase of testData.results.test_cases) {
    const paramsJson = JSON.stringify(testCase.params, null, 4);
    await page.locator('#lingo-app-params-textarea').fill(paramsJson);
    await page.getByRole('button', { name: 'Run' }).click();
    
    await expect(page.locator('#lingo-app')).toContainText(`"value": ${testCase.result.value}`);
    await expect(page.locator('#lingo-app')).toContainText(`"type": "${testCase.result.type}"`);
  }
});

test('test - basic_math script', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  
  // Load test data
  const response = await page.request.get('http://127.0.0.1:8000/data/lingo/scripts/basic_math_test_data.json');
  const testData = await response.json();
  
  // Test with default params
  await page.locator('#spec-select').selectOption('data/lingo/scripts/basic_math.json');
  await expect(page.locator('#lingo-app')).toContainText(`"value": ${testData.results.default.value}`);
  await expect(page.locator('#lingo-app')).toContainText(`"type": "${testData.results.default.type}"`);
  
  // Test each test case
  for (const testCase of testData.results.test_cases) {
    const paramsJson = JSON.stringify(testCase.params, null, 4);
    await page.locator('#lingo-app-params-textarea').fill(paramsJson);
    await page.getByRole('button', { name: 'Run' }).click();
    
    await expect(page.locator('#lingo-app')).toContainText(`"value": ${testCase.result.value}`);
    await expect(page.locator('#lingo-app')).toContainText(`"type": "${testCase.result.type}"`);
  }
});

test('test - all_param_types script', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  
  // Load test data
  const response = await page.request.get('http://127.0.0.1:8000/data/lingo/scripts/all_param_types_test_data.json');
  const testData = await response.json();
  
  // Test with default params
  await page.locator('#spec-select').selectOption('data/lingo/scripts/all_param_types.json');
  await expect(page.locator('#lingo-app')).toContainText(`"value": ${testData.results.default.value}`);
  await expect(page.locator('#lingo-app')).toContainText(`"type": "${testData.results.default.type}"`);
  
  // Test each test case
  for (const testCase of testData.results.test_cases) {
    const paramsJson = JSON.stringify(testCase.params, null, 4);
    await page.locator('#lingo-app-params-textarea').fill(paramsJson);
    await page.getByRole('button', { name: 'Run' }).click();
    
    await expect(page.locator('#lingo-app')).toContainText(`"value": ${testCase.result.value}`);
    await expect(page.locator('#lingo-app')).toContainText(`"type": "${testCase.result.type}"`);
  }
});

test('test - branch_example script', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  
  // Load test data
  const response = await page.request.get('http://127.0.0.1:8000/data/lingo/scripts/branch_example_test_data.json');
  const testData = await response.json();
  
  // Test with default params
  await page.locator('#spec-select').selectOption('data/lingo/scripts/branch_example.json');
  await expect(page.locator('#lingo-app')).toContainText(`"value": "${testData.results.default.value}"`);
  await expect(page.locator('#lingo-app')).toContainText(`"type": "${testData.results.default.type}"`);
  
  // Test each test case
  for (const testCase of testData.results.test_cases) {
    const paramsJson = JSON.stringify(testCase.params, null, 4);
    await page.locator('#lingo-app-params-textarea').fill(paramsJson);
    await page.getByRole('button', { name: 'Run' }).click();
    
    await expect(page.locator('#lingo-app')).toContainText(`"value": "${testCase.result.value}"`);
    await expect(page.locator('#lingo-app')).toContainText(`"type": "${testCase.result.type}"`);
  }
});

test('test - switch_example script', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  
  // Load test data
  const response = await page.request.get('http://127.0.0.1:8000/data/lingo/scripts/switch_example_test_data.json');
  const testData = await response.json();
  
  // Test with default params
  await page.locator('#spec-select').selectOption('data/lingo/scripts/switch_example.json');
  await expect(page.locator('#lingo-app')).toContainText(`"value": "${testData.results.default.value}"`);
  await expect(page.locator('#lingo-app')).toContainText(`"type": "${testData.results.default.type}"`);
  
  // Test each test case
  for (const testCase of testData.results.test_cases) {
    const paramsJson = JSON.stringify(testCase.params, null, 4);
    await page.locator('#lingo-app-params-textarea').fill(paramsJson);
    await page.getByRole('button', { name: 'Run' }).click();
    
    await expect(page.locator('#lingo-app')).toContainText(`"value": "${testCase.result.value}"`);
    await expect(page.locator('#lingo-app')).toContainText(`"type": "${testCase.result.type}"`);
  }
});