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
  await expect(page.locator('a[href="/my-module-a/my-model-a"]')).toContainText('my-model-a');
  await expect(page.locator('a[href="/my-module-a/my-model-b"]')).toContainText('my-model-b');

  // Check that the page says "Available Ops:"
  await expect(page.locator('#lingo-app')).toContainText(':: available operations');
  
  // Check that links are generated for each op with concat working
  await expect(page.locator('a[href="/my-module-a/my-op-a"]')).toContainText('my-op-a');
  await expect(page.locator('a[href="/my-module-a/my-op-b"]')).toContainText('my-op-b');
  
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
  await expect(page.locator('a[href="/users/user"]')).toContainText('user');
  await expect(page.locator('a[href="/users/profile"]')).toContainText('profile');
  await expect(page.locator('a[href="/users/settings"]')).toContainText('settings');

  // Check that the page says "Available Ops:"
  await expect(page.locator('#lingo-app')).toContainText(':: available operations');
  
  // Check that links are generated for each op with concat working
  await expect(page.locator('a[href="/users/create_user"]')).toContainText('create_user');
  await expect(page.locator('a[href="/users/delete_user"]')).toContainText('delete_user');
  await expect(page.locator('a[href="/users/update_profile"]')).toContainText('update_profile');
});

test('test - structs page', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/structs.json');

  // Check for Individual Structs heading
  await expect(page.locator('h1').first()).toContainText('Individual Structs');

  // Check for struct tables
  const tables = page.locator('table');
  // We should have many tables: individual structs (12) + list tables (3) = 15 total
  await expect(tables).toHaveCount(15);

  // Check first struct table (primitives: str, int, bool - hardcoded)
  const firstTable = tables.nth(0);
  await expect(firstTable.locator('th').nth(0)).toContainText('key');
  await expect(firstTable.locator('th').nth(1)).toContainText('value');
  await expect(firstTable.locator('td').filter({ hasText: 'color' })).toBeVisible();
  await expect(firstTable.locator('td').filter({ hasText: 'red' })).toBeVisible();
  await expect(firstTable.locator('td').filter({ hasText: 'amount' })).toBeVisible();
  await expect(firstTable.locator('td').filter({ hasText: '10' })).toBeVisible();
  await expect(firstTable.locator('td').filter({ hasText: 'in_stock' })).toBeVisible();
  await expect(firstTable.locator('td').filter({ hasText: 'true' })).toBeVisible();

  // Check second struct table (primitives with typed values)
  const secondTable = tables.nth(1);
  await expect(secondTable.locator('td').filter({ hasText: 'green' })).toBeVisible();
  await expect(secondTable.locator('td').filter({ hasText: '20' })).toBeVisible();

  // Check third struct table (no headers, with scripted values)
  const thirdTable = tables.nth(2);
  // This table should NOT have header row
  await expect(thirdTable.locator('th')).toHaveCount(0);
  await expect(thirdTable.locator('td').filter({ hasText: 'blue' })).toBeVisible();
  await expect(thirdTable.locator('td').filter({ hasText: '20' })).toBeVisible(); // 5 + 15 = 20

  // Check float/datetime struct (hardcoded)
  const floatDatetimeTable = tables.nth(3);
  await expect(floatDatetimeTable.locator('td').filter({ hasText: 'price' })).toBeVisible();
  await expect(floatDatetimeTable.locator('td').filter({ hasText: '19.99' })).toBeVisible();
  await expect(floatDatetimeTable.locator('td').filter({ hasText: 'created_at' })).toBeVisible();
  await expect(floatDatetimeTable.locator('td').filter({ hasText: '2024-01-15T10:30:00' })).toBeVisible();

  // Check list values struct
  const listStruct = tables.nth(6);
  await expect(listStruct.locator('td').filter({ hasText: 'tags' })).toBeVisible();
  // Lists should be displayed as comma-separated strings
  await expect(listStruct).toContainText('urgent');

  // Check for List of Structs heading
  await expect(page.locator('h1').filter({ hasText: 'List of Structs' })).toBeVisible();

  // Check the first list table (basic types) - this is table index 12
  const listTable = tables.nth(12);
  await expect(listTable.locator('th').filter({ hasText: 'Color' })).toBeVisible();
  await expect(listTable.locator('th').filter({ hasText: 'Amount' })).toBeVisible();
  await expect(listTable.locator('th').filter({ hasText: 'In Stock' })).toBeVisible();

  // Check rows in list table
  const rows = listTable.locator('tbody tr');
  await expect(rows).toHaveCount(3);
  
  // First row
  await expect(rows.nth(0).locator('td').nth(0)).toContainText('red');
  await expect(rows.nth(0).locator('td').nth(1)).toContainText('10');
  await expect(rows.nth(0).locator('td').nth(2)).toContainText('true');
  
  // Second row
  await expect(rows.nth(1).locator('td').nth(0)).toContainText('green');
  await expect(rows.nth(1).locator('td').nth(1)).toContainText('20');
  await expect(rows.nth(1).locator('td').nth(2)).toContainText('false');
  
  // Third row
  await expect(rows.nth(2).locator('td').nth(0)).toContainText('blue');
  await expect(rows.nth(2).locator('td').nth(1)).toContainText('20');
  await expect(rows.nth(2).locator('td').nth(2)).toContainText('true');
});

test('test - forms page', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/forms.json');

  // Check heading
  await expect(page.locator('h1')).toContainText('Forms');

  // Check that basic form fields are visible with correct types
  const colorInput = page.locator('input[type="text"]').first();
  await expect(colorInput).toBeVisible();
  await expect(colorInput).toHaveValue('blue');
  
  const amountInput = page.locator('input[type="number"]').first();
  await expect(amountInput).toBeVisible();
  await expect(amountInput).toHaveValue('42');
  
  const inStockCheckbox = page.locator('input[type="checkbox"]').first();
  await expect(inStockCheckbox).toBeVisible();
  await expect(inStockCheckbox).not.toBeChecked();
  
  const priceInput = page.locator('input[type="number"]').nth(1);
  await expect(priceInput).toBeVisible();
  await expect(priceInput).toHaveValue('19.99');
  
  // Check enum field (category dropdown)
  const categorySelect = page.locator('table select').first();
  await expect(categorySelect).toBeVisible();
  await expect(categorySelect).toHaveValue('electronics');
  
  // Check datetime field (release date)
  const releaseDateInput = page.locator('input[type="datetime-local"]').first();
  await expect(releaseDateInput).toBeVisible();
  await expect(releaseDateInput).toHaveValue('2024-01-15T10:30');
  
  // Check foreign key field (supplier_id)
  const supplierIdInput = page.getByPlaceholder('Enter ID');
  await expect(supplierIdInput).toBeVisible();
  await expect(supplierIdInput).toHaveValue('1');
  
  // Check list field inputs are visible
  await expect(page.getByPlaceholder('Enter text')).toBeVisible(); // tags list
  await expect(page.getByPlaceholder('Enter integer')).toBeVisible(); // ratings list
  
  // Check submit button
  await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();
  
  // Test form interaction - change basic values
  await colorInput.fill('red');
  await amountInput.fill('100');
  await inStockCheckbox.check();
  await priceInput.fill('29.99');
  
  // Verify the checkbox is now checked
  await expect(inStockCheckbox).toBeChecked();
  
  // Test adding items to a list
  const tagsInput = page.getByPlaceholder('Enter text');
  await tagsInput.fill('organic');
  await page.getByRole('button', { name: 'Add' }).first().click();
  
  // Verify the tag was added and is displayed
  await expect(page.locator('text=organic')).toBeVisible();
  
  // Verify the remove button is visible
  await expect(page.getByRole('button', { name: '×' }).first()).toBeVisible();
  
  // Test adding another tag using Enter key
  await tagsInput.fill('eco-friendly');
  await tagsInput.press('Enter');
  
  // Verify both tags are displayed
  await expect(page.locator('text=organic')).toBeVisible();
  await expect(page.locator('text=eco-friendly')).toBeVisible();
  
  // Test removing a tag
  await page.getByRole('button', { name: '×' }).first().click();
  
  // Verify one tag was removed (eco-friendly should still be there)
  await expect(page.locator('text=eco-friendly')).toBeVisible();
  
  // Click submit button - this logs to console
  await page.getByRole('button', { name: 'Submit' }).click();
});

test('test - formatting page', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/formatting.json');

  // Check headings within the lingo app
  const lingoApp = page.locator('#lingo-app');
  await expect(lingoApp.locator('h1')).toContainText('The World with a Pink Sky');
  await expect(lingoApp.locator('h2')).toContainText('A Beautiful Adventure in Formatting');

  // Check that styled text elements are present with correct styles
  
  // Check for bold text
  const boldText = lingoApp.locator('span').filter({ hasText: 'far' }).first();
  await expect(boldText).toHaveCSS('font-weight', '700'); // bold = 700

  // Check for italic text
  const italicText = lingoApp.locator('span').filter({ hasText: 'far' }).nth(1);
  await expect(italicText).toHaveCSS('font-style', 'italic');

  // Check for underline text
  const underlineText = lingoApp.locator('span').filter({ hasText: 'away' });
  await expect(underlineText).toHaveCSS('text-decoration', /underline/);

  // Check for strikethrough text
  const strikethroughText = lingoApp.locator('span').filter({ hasText: 'cross things out.' });
  await expect(strikethroughText).toHaveCSS('text-decoration', /line-through/);

  // Check for colored text - pink
  const pinkText = lingoApp.locator('span').filter({ hasText: 'pink' }).first();
  await expect(pinkText).toHaveCSS('color', 'rgb(255, 192, 203)'); // pink in RGB

  // Check for multiple styles combined (bold + italic + underline + color)
  const multiStyleText = lingoApp.locator('span').filter({ hasText: 'happily.' }).first();
  await expect(multiStyleText).toHaveCSS('font-weight', '700'); // bold
  await expect(multiStyleText).toHaveCSS('font-style', 'italic');
  await expect(multiStyleText).toHaveCSS('text-decoration', /underline/);
  await expect(multiStyleText).toHaveCSS('color', 'rgb(128, 0, 128)'); // purple in RGB

  // Check colored list items
  const redListItem = lingoApp.locator('li').filter({ hasText: 'Red' }).locator('span');
  await expect(redListItem).toHaveCSS('color', 'rgb(255, 0, 0)'); // red in RGB

  const greenListItem = lingoApp.locator('li').filter({ hasText: 'Green' }).locator('span');
  await expect(greenListItem).toHaveCSS('color', 'rgb(0, 128, 0)'); // green in RGB

  // Check special color names (dark_gray, light_gray)
  const darkGrayListItem = lingoApp.locator('li').filter({ hasText: 'Dark Gray' }).locator('span');
  await expect(darkGrayListItem).toHaveCSS('color', 'rgb(169, 169, 169)'); // darkgray in RGB

  const lightGrayListItem = lingoApp.locator('li').filter({ hasText: 'Light Gray' }).locator('span');
  await expect(lightGrayListItem).toHaveCSS('color', 'rgb(211, 211, 211)'); // lightgray in RGB
});

test('test - builtin mapp model page', async ({ page }) => {
  // Listen for console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/builtin-mapp-model.json');

  // Wait a bit for rendering to complete
  await page.waitForTimeout(1000);

  // Check heading is present
  const lingoApp = page.locator('#lingo-app');
  await expect(lingoApp.locator('h2')).toContainText(':: My Lingo Project :: my-module-a :: my-model-a');
  
  // Check that model-list section exists
  await expect(lingoApp.locator('h3')).toContainText(':: list of models');
  
  // Check that "Create New Model" button is visible
  await expect(page.getByRole('button', { name: 'Create New Model' })).toBeVisible();
  
  // Check that model status is displayed
  await expect(lingoApp.locator('.model-status, .model-list-status')).toBeVisible();
  
  // Verify no critical console errors occurred during rendering
  const criticalErrors = consoleErrors.filter(err => 
    err.includes('undefined') || err.includes('is not a function') || err.includes('Cannot read')
  );
  expect(criticalErrors).toHaveLength(0);
});