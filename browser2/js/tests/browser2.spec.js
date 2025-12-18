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

test('test - return types', async ({ page }) => {
  await page.goto('http://localhost:8000/', { waitUntil: 'networkidle' });
  await page.locator('#spec-select').selectOption('data/lingo/pages/return-types.json');
  await expect(page.locator('span')).toContainText('{ "type": "int", "value": 16 }');
});

test('test - functions', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions.json');

  await expect(page.locator('h1')).toContainText('Function Tests');


  const expectedText = [
	'Comparison Functions:',
	'eq(5, 5) = true',
    'eq(5, 3) = false',
    'ne(5, 3) = true',
	'ne(5, 5) = false',
	'lt(3, 5) = true',
	'lt(5, 3) = false',
	'le(5, 5) = true',
	'le(7, 5) = false',
	'gt(7, 5) = true',
	'gt(3, 5) = false',
	'ge(5, 5) = true',
	'ge(3, 5) = false',

	'Boolean Functions:',
	'bool(1) = true',
	'bool(0) = false',
	'not(true) = false',
	'not(false) = true',
	'neg(5) = -5',
	'and(true, true) = true',
	'and(true, false) = false',
	'or(false, true) = true',
	'or(false, false) = false',

	'Int Functions:',
	'int(42.7) = 42',
	'int(\'2A\', base=16) = 42',

	'Float Functions:',
	'float(\'1e-003\') = 0.001',
	'round(3.14159) = 3',
	'round(3.14159, ndigits=3) = 3.142',


	'String Functions:',
	'str(123) = 123',
	'join(\'-\', [\'a\',\'b\',\'c\']) = a-b-c',
	'concat([\'hello\', \' \', \'world\']) = hello world',

	'Math Functions:',
	'add(10, 5) = 15',
	'sub(10, 3) = 7',
	'mul(4, 7) = 28',
	'div(15, 3) = 5',
	'floordiv(15, 2) = 7',
	'mod(15, 4) = 3',
	'pow(2, 3) = 8',
	'min(3, 7) = 3',
	'max(3, 7) = 7',
	'abs(-10) = 10',

	'Sequence Functions:',
	'len([1,2,3,4,5]) = 5',
	'len(\'hello\') = 5',
	'range(5) = 0, 1, 2, 3, 4',
	'range(1, 7) = 1, 2, 3, 4, 5, 6',
	'range(0, 10, 2) = 0, 2, 4, 6, 8',
	'slice([0,1,2,3,4], stop=2) = 0, 1',
	'slice([0,1,2,3,4,5,6], start=2, stop=5) = 2, 3, 4',
	'slice([0,1,2,3,4], start=1, stop=4, step=2) = 1, 3',
	'any([true, false]) = true',
	'any([false, false]) = false',
	'all([true, true]) = true',
	'all([true, false]) = false',
	'sum([1,2,3], start=0) = 6',
	'sum([1,2,3], start=10) = 16',
	'sorted([5,2,9]) = 2, 5, 9',

	'Sequence Operations:',
	'map(add(item, 10), [1,2,3,4,5]) = 11, 12, 13, 14, 15',
	'filter(gt(item, 3), [1,2,3,4,5,6,7]) = 4, 5, 6, 7',
	'dropwhile(lt(item, 4), [1,2,3,4,5,6,7]) = 4, 5, 6, 7',
	'takewhile(lt(item, 4), [1,2,3,4,5,6,7]) = 1, 2, 3',
	'reversed([1,2,3]) = 3, 2, 1',
	'accumulate([1,2,3,4], add) = 1, 3, 6, 10',
	'accumulate([1,2,3,4], add, initial=10) = 10, 11, 13, 16, 20',
	'reduce([1,2,3,4], add) = 10',
	'reduce([1,2,3,4], add, initial=10) = 20',

	'Date and Time Functions:',
	'current.weekday() = ',
	'datetime.now() = ',


	'Random Functions:',
	'random.randint(1, 10) = '
  ]

  for (const text of expectedText) {
	await expect(page.locator('#lingo-app')).toContainText(text);
  }


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


test('test - builtin mapp project page', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/builtin-mapp-project.json');

  //
  // default params
  //

  // Check that the heading contains the project name
  await expect(page.locator('h1')).toContainText(':: My Lingo Project');
  
  // Check that the page says "Available Modules:"
  await expect(page.locator('#lingo-app')).toContainText(':: available modules');
  
  // Check that links are generated for each module with concat working
  await expect(page.locator('a[href="/my-module-a"]')).toContainText('my-module-a');
  await expect(page.locator('a[href="/my-module-b"]')).toContainText('my-module-b');
  
  // 
  // custom params
  //

  const params = {
    "project_name": "My Social App",
    "module_names": ["users", "posts", "comments"]
  };
  await page.locator('#lingo-app-params-textarea').fill(JSON.stringify(params, null, 4));
  await page.getByRole('button', { name: 'Run' }).click();
  
  // Check that the heading contains the project name
  await expect(page.locator('h1')).toContainText(':: My Social App');
  
  // Check that the page says "Available Modules:"
  await expect(page.locator('#lingo-app')).toContainText(':: available modules');
  
  // Check that links are generated for each module with concat working
  await expect(page.locator('a[href="/users"]')).toContainText('users');
  await expect(page.locator('a[href="/posts"]')).toContainText('posts');
  await expect(page.locator('a[href="/comments"]')).toContainText('comments');
});

test('test - builtin mapp module page', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/builtin-mapp-module.json');

  //
  // default params
  //

  // Check that the heading contains the project name
  await expect(page.locator('h1')).toContainText(':: My Lingo Project :: my-module-a');
  
  // Check that the page says "Available Models:"
  await expect(page.locator('#lingo-app')).toContainText(':: available models');
  
  // Check that links are generated for each model with concat working
  await expect(page.locator('a[href="/my-model-a"]')).toContainText('my-model-a');
  await expect(page.locator('a[href="/my-model-b"]')).toContainText('my-model-b');

  // Check that the page says "Available Ops:"
  await expect(page.locator('#lingo-app')).toContainText(':: available operations');
  
  // Check that links are generated for each op with concat working
  await expect(page.locator('a[href="/my-op-a"]')).toContainText('my-op-a');
  await expect(page.locator('a[href="/my-op-b"]')).toContainText('my-op-b');
  
  // 
  // custom params
  //

  const params = {
    "project_name": "My Social App",
    "module_name": "users",
    "model_names": ["user", "profile", "settings"],
    "op_names": ["create_user", "delete_user", "update_profile"]
  };
  await page.locator('#lingo-app-params-textarea').fill(JSON.stringify(params, null, 4));
  await page.getByRole('button', { name: 'Run' }).click();
  
  // Check that the heading contains the project name
  await expect(page.locator('h1')).toContainText(':: My Social App :: users');
  
  // Check that the page says "Available Models:"
  await expect(page.locator('#lingo-app')).toContainText(':: available models');
  
  // Check that links are generated for each model with concat working
  await expect(page.locator('a[href="/user"]')).toContainText('user');
  await expect(page.locator('a[href="/profile"]')).toContainText('profile');
  await expect(page.locator('a[href="/settings"]')).toContainText('settings');

  // Check that the page says "Available Ops:"
  await expect(page.locator('#lingo-app')).toContainText(':: available operations');
  
  // Check that links are generated for each op with concat working
  await expect(page.locator('a[href="/create_user"]')).toContainText('create_user');
  await expect(page.locator('a[href="/delete_user"]')).toContainText('delete_user');
  await expect(page.locator('a[href="/update_profile"]')).toContainText('update_profile');
});