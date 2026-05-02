import { test, expect } from '@playwright/test';

test('test - hello world', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await expect(page.locator('h1')).toContainText('hello.world');
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
  await expect(page.locator('span')).toContainText('16');
});

test('test - functions-comparison', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-comparison.json');

  await expect(page.locator('h1')).toContainText('Comparison Functions');

  const expectedText = [
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
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-bool', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-bool.json');

  await expect(page.locator('h1')).toContainText('Bool Functions');

  const expectedText = [
    'bool(1) = true',
    'bool(0) = false',
    'not(true) = false',
    'not(false) = true',
    'and(true, true) = true',
    'and(true, false) = false',
    'or(false, true) = true',
    'or(false, false) = false',
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-int', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-int.json');

  await expect(page.locator('h1')).toContainText('Int Functions');

  const expectedText = [
    'neg(5) = -5',
    'int(42.7) = 42',
    'int(\'2A\', base=16) = 42',
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-float', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-float.json');

  await expect(page.locator('h1')).toContainText('Float Functions');

  const expectedText = [
    'float(\'1e-003\') = 0.001',
    'round(3.14159) = 3',
    'round(3.14159, ndigits=3) = 3.142',
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-str', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-str.json');

  await expect(page.locator('h1')).toContainText('Str Functions');

  const expectedText = [
    'str(123) = 123',
    'join(\'-\', [\'a\',\'b\',\'c\']) = a-b-c',
    'concat([\'hello\', \' \', \'world\']) = hello world',
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-struct', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-struct.json');

  await expect(page.locator('h1')).toContainText('Struct Functions');

  const expectedText = [
    'key(state.source_struct, \'x_bool\') = true',
    'key(state.source_struct, \'x_int\') = 42',
    'key(state.source_struct, \'x_float\') = 3.14',
    'key(state.source_struct, \'x_str\') = hello.world',
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});


test('test - functions-math', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-math.json');

  await expect(page.locator('h1')).toContainText('Math Functions');

  const expectedText = [
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
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-sequence', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-sequence.json');

  await expect(page.locator('h1')).toContainText('Sequence Functions');

  const expectedText = [
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
    'sorted([\'banana\', \'apple\', \'cherry\']) = apple, banana, cherry'
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-sequence-ops', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-sequence-ops.json');

  await expect(page.locator('h1')).toContainText('Sequence Ops Functions');

  const expectedText = [
    'map(add(item, 10), [1,2,3,4,5]) = 11, 12, 13, 14, 15',
    'filter(gt(item, 3), [1,2,3,4,5,6,7]) = 4, 5, 6, 7',
    'dropwhile(lt(item, 4), [1,2,3,4,5,6,7]) = 4, 5, 6, 7',
    'takewhile(lt(item, 4), [1,2,3,4,5,6,7]) = 1, 2, 3',
    'reversed([1,2,3]) = 3, 2, 1',
    'accumulate([1,2,3,4], add) = 1, 3, 6, 10',
    'accumulate([1,2,3,4], add, initial=10) = 10, 11, 13, 16, 20',
    'reduce([1,2,3,4], add) = 10',
    'reduce([1,2,3,4], add, initial=10) = 20',
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-datetime', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-datetime.json');

  await expect(page.locator('h1')).toContainText('Date and Time Functions');

  const expectedText = [
    'current.weekday() = ',
    'datetime.now() = ',
  ];

  for (const text of expectedText) {
    await expect(page.locator('#lingo-app')).toContainText(text);
  }
});

test('test - functions-random', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-random.json');

  await expect(page.locator('h1')).toContainText('Random Functions');

  await expect(page.locator('#lingo-app')).toContainText('random.randint(1, 10) = ');
});

test('test - functions-client', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/functions-client.json');

  await expect(page.locator('h1')).toContainText('Client Functions');
  await expect(page.locator('#lingo-app')).toContainText('client.reload()');

  await Promise.all([
    page.waitForEvent('load'),
    page.getByRole('button', { name: 'Reload Page' }).click()
  ]);
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

test('test - primitive_types script', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  
  // Load test data
  const response = await page.request.get('http://127.0.0.1:8000/data/lingo/scripts/primitive_types_test_data.json');
  const testData = await response.json();
  
  // Test with default params
  await page.locator('#spec-select').selectOption('data/lingo/scripts/primitive_types.json');
  await expect(page.locator('#lingo-app')).toContainText(testData.results.default.value);

  
  // Test each test case
  for (const testCase of testData.results.test_cases) {
    const paramsJson = JSON.stringify(testCase.params, null, 4);
    await page.locator('#lingo-app-params-textarea').fill(paramsJson);
    await page.getByRole('button', { name: 'Run' }).click();
    
    await expect(page.locator('#lingo-app')).toContainText(testCase.result.value);
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

test('test - structs page', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/structs.json');

  // Check all section headings (scoped to #lingo-app to exclude static page elements)
  const lingoApp = page.locator('#lingo-app');
  await expect(lingoApp.locator('h1').nth(0)).toContainText('Individual Structs');
  await expect(lingoApp.locator('h1').nth(1)).toContainText('List of Structs');
  await expect(lingoApp.locator('h2').nth(0)).toContainText('Primitives: str, int, bool');
  await expect(lingoApp.locator('h2').nth(1)).toContainText('Primitives: float, datetime');
  await expect(lingoApp.locator('h2').nth(2)).toContainText('Lists of primitives');
  await expect(lingoApp.locator('h2').nth(3)).toContainText('Lists with datetime elements');
  await expect(lingoApp.locator('h2').nth(4)).toContainText('Mixed struct with all types');
  await expect(lingoApp.locator('h2').nth(5)).toContainText('Basic types in table');

  // Check total table count: individual structs (12) + list tables (4) = 16
  const tables = page.locator('table');
  await expect(tables).toHaveCount(16);

  //
  // primitives: str, int, bool
  //

  // Table 0: str/int/bool hardcoded - with key/value headers
  const primitivesHardcodedTable = tables.nth(0);
  await expect(primitivesHardcodedTable.locator('th').nth(0)).toContainText('key');
  await expect(primitivesHardcodedTable.locator('th').nth(1)).toContainText('value');
  await expect(primitivesHardcodedTable.locator('td').filter({ hasText: 'color' })).toBeVisible();
  await expect(primitivesHardcodedTable.locator('td').filter({ hasText: 'red' })).toBeVisible();
  await expect(primitivesHardcodedTable.locator('td').filter({ hasText: 'amount' })).toBeVisible();
  await expect(primitivesHardcodedTable.locator('td').filter({ hasText: '10' })).toBeVisible();
  await expect(primitivesHardcodedTable.locator('td').filter({ hasText: 'in_stock' })).toBeVisible();
  await expect(primitivesHardcodedTable.locator('td').filter({ hasText: 'true' })).toBeVisible();

  // Table 1: str/int/bool typed - with key/value headers
  const primitiveTypedTable = tables.nth(1);
  await expect(primitiveTypedTable.locator('th').nth(0)).toContainText('key');
  await expect(primitiveTypedTable.locator('th').nth(1)).toContainText('value');
  await expect(primitiveTypedTable.locator('td').filter({ hasText: 'color' })).toBeVisible();
  await expect(primitiveTypedTable.locator('td').filter({ hasText: 'green' })).toBeVisible();
  await expect(primitiveTypedTable.locator('td').filter({ hasText: 'amount' })).toBeVisible();
  await expect(primitiveTypedTable.locator('td').filter({ hasText: '20' })).toBeVisible();
  await expect(primitiveTypedTable.locator('td').filter({ hasText: 'in_stock' })).toBeVisible();
  await expect(primitiveTypedTable.locator('td').filter({ hasText: 'true' })).toBeVisible();

  // Table 2: str/int/bool dynamic - NO headers
  const primitiveDynamicTable = tables.nth(2);
  await expect(primitiveDynamicTable.locator('th')).toHaveCount(0);
  await expect(primitiveDynamicTable.locator('td').filter({ hasText: 'color' })).toBeVisible();
  await expect(primitiveDynamicTable.locator('td').filter({ hasText: 'blue' })).toBeVisible();
  await expect(primitiveDynamicTable.locator('td').filter({ hasText: 'amount' })).toBeVisible();
  await expect(primitiveDynamicTable.locator('td').filter({ hasText: '20' })).toBeVisible(); // add(5, 15) = 20
  await expect(primitiveDynamicTable.locator('td').filter({ hasText: 'in_stock' })).toBeVisible();
  await expect(primitiveDynamicTable.locator('td').filter({ hasText: 'true' })).toBeVisible(); // eq(1, 1) = true

  //
  // primitives: float, datetime
  //

  // Table 3: float/datetime hardcoded - with key/value headers
  const floatDatetimeHardcodedTable = tables.nth(3);
  await expect(floatDatetimeHardcodedTable.locator('th').nth(0)).toContainText('key');
  await expect(floatDatetimeHardcodedTable.locator('th').nth(1)).toContainText('value');
  await expect(floatDatetimeHardcodedTable.locator('td').filter({ hasText: 'price' })).toBeVisible();
  await expect(floatDatetimeHardcodedTable.locator('td').filter({ hasText: '19.99' })).toBeVisible();
  await expect(floatDatetimeHardcodedTable.locator('td').filter({ hasText: 'weight' })).toBeVisible();
  await expect(floatDatetimeHardcodedTable.locator('td').filter({ hasText: '2.5' })).toBeVisible();
  await expect(floatDatetimeHardcodedTable.locator('td').filter({ hasText: 'created_at' })).toBeVisible();
  await expect(floatDatetimeHardcodedTable.locator('td').filter({ hasText: '2024-01-15T10:30:00' })).toBeVisible();
  await expect(floatDatetimeHardcodedTable.locator('td').filter({ hasText: 'updated_at' })).toBeVisible();
  await expect(floatDatetimeHardcodedTable.locator('td').filter({ hasText: '2024-06-20T14:45:30' })).toBeVisible();

  // Table 4: float/datetime typed - with key/value headers
  const floatDatetimeTypedTable = tables.nth(4);
  await expect(floatDatetimeTypedTable.locator('th').nth(0)).toContainText('key');
  await expect(floatDatetimeTypedTable.locator('th').nth(1)).toContainText('value');
  await expect(floatDatetimeTypedTable.locator('td').filter({ hasText: 'price' })).toBeVisible();
  await expect(floatDatetimeTypedTable.locator('td').filter({ hasText: '29.99' })).toBeVisible();
  await expect(floatDatetimeTypedTable.locator('td').filter({ hasText: 'weight' })).toBeVisible();
  await expect(floatDatetimeTypedTable.locator('td').filter({ hasText: '3.75' })).toBeVisible();
  await expect(floatDatetimeTypedTable.locator('td').filter({ hasText: 'created_at' })).toBeVisible();
  await expect(floatDatetimeTypedTable.locator('td').filter({ hasText: '2023-12-01T08:00:00' })).toBeVisible();
  await expect(floatDatetimeTypedTable.locator('td').filter({ hasText: 'updated_at' })).toBeVisible();
  await expect(floatDatetimeTypedTable.locator('td').filter({ hasText: '2024-03-15T16:20:10' })).toBeVisible();

  // Table 5: float/datetime dynamic - NO headers
  const floatDatetimeDynamicTable = tables.nth(5);
  await expect(floatDatetimeDynamicTable.locator('th')).toHaveCount(0);
  await expect(floatDatetimeDynamicTable.locator('td').filter({ hasText: 'price' })).toBeVisible();
  await expect(floatDatetimeDynamicTable.locator('td').filter({ hasText: '19.99' })).toBeVisible(); // add(10.5, 9.49) = 19.99
  await expect(floatDatetimeDynamicTable.locator('td').filter({ hasText: 'weight' })).toBeVisible();
  await expect(floatDatetimeDynamicTable.locator('td').filter({ hasText: '2.5' })).toBeVisible(); // div(10.0, 4.0) = 2.5

  //
  // lists of primitives
  //

  // Table 6: lists of primitives hardcoded - with key/value headers
  const listOfPrimitivesHardcoded = tables.nth(6);
  await expect(listOfPrimitivesHardcoded.locator('th').nth(0)).toContainText('key');
  await expect(listOfPrimitivesHardcoded.locator('th').nth(1)).toContainText('value');
  await expect(listOfPrimitivesHardcoded.locator('td').filter({ hasText: 'tags' })).toBeVisible();
  await expect(listOfPrimitivesHardcoded).toContainText('urgent');
  await expect(listOfPrimitivesHardcoded).toContainText('important');
  await expect(listOfPrimitivesHardcoded).toContainText('review');
  await expect(listOfPrimitivesHardcoded.locator('td').filter({ hasText: 'scores' })).toBeVisible();
  await expect(listOfPrimitivesHardcoded).toContainText('85');
  await expect(listOfPrimitivesHardcoded).toContainText('92');
  await expect(listOfPrimitivesHardcoded.locator('td').filter({ hasText: 'measurements' })).toBeVisible();
  await expect(listOfPrimitivesHardcoded).toContainText('3.14');

  // Table 7: lists of primitives typed - with key/value headers
  const listOfPrimitivesTyped = tables.nth(7);
  await expect(listOfPrimitivesTyped.locator('th').nth(0)).toContainText('key');
  await expect(listOfPrimitivesTyped.locator('th').nth(1)).toContainText('value');
  await expect(listOfPrimitivesTyped.locator('td').filter({ hasText: 'tags' })).toBeVisible();
  await expect(listOfPrimitivesTyped).toContainText('electronics');
  await expect(listOfPrimitivesTyped).toContainText('gadgets');
  await expect(listOfPrimitivesTyped).toContainText('tech');
  await expect(listOfPrimitivesTyped.locator('td').filter({ hasText: 'scores' })).toBeVisible();
  await expect(listOfPrimitivesTyped).toContainText('88');
  await expect(listOfPrimitivesTyped).toContainText('91');
  await expect(listOfPrimitivesTyped).toContainText('79');
  await expect(listOfPrimitivesTyped.locator('td').filter({ hasText: 'flags' })).toBeVisible();
  await expect(listOfPrimitivesTyped.locator('td').filter({ hasText: 'measurements' })).toBeVisible();
  await expect(listOfPrimitivesTyped).toContainText('2.5');
  await expect(listOfPrimitivesTyped).toContainText('3.7');
  await expect(listOfPrimitivesTyped).toContainText('1.2');

  // Table 8: lists of primitives dynamic - NO headers
  const listOfPrimitivesDynamic = tables.nth(8);
  await expect(listOfPrimitivesDynamic.locator('th')).toHaveCount(0);
  await expect(listOfPrimitivesDynamic.locator('td').filter({ hasText: 'tags' })).toBeVisible();
  await expect(listOfPrimitivesDynamic.locator('td').filter({ hasText: 'total_score' })).toBeVisible();
  await expect(listOfPrimitivesDynamic).toContainText('1');
  await expect(listOfPrimitivesDynamic).toContainText('2');
  await expect(listOfPrimitivesDynamic).toContainText('3');
  await expect(listOfPrimitivesDynamic).toContainText('60'); // sum([10, 20, 30], start=0) = 60

  //
  // lists with datetime elements
  //

  // Table 9: datetime lists hardcoded - with key/value headers
  const datetimeListsHardcoded = tables.nth(9);
  await expect(datetimeListsHardcoded.locator('th').nth(0)).toContainText('key');
  await expect(datetimeListsHardcoded.locator('th').nth(1)).toContainText('value');
  await expect(datetimeListsHardcoded.locator('td').filter({ hasText: 'event_dates' })).toBeVisible();
  await expect(datetimeListsHardcoded).toContainText('2024-01-01T00:00:00');
  await expect(datetimeListsHardcoded).toContainText('2024-07-04T12:00:00');
  await expect(datetimeListsHardcoded.locator('td').filter({ hasText: 'meeting_times' })).toBeVisible();
  await expect(datetimeListsHardcoded).toContainText('2024-03-15T09:00:00');

  // Table 10: datetime lists typed - with key/value headers
  const datetimeListsTyped = tables.nth(10);
  await expect(datetimeListsTyped.locator('th').nth(0)).toContainText('key');
  await expect(datetimeListsTyped.locator('th').nth(1)).toContainText('value');
  await expect(datetimeListsTyped.locator('td').filter({ hasText: 'event_dates' })).toBeVisible();
  await expect(datetimeListsTyped).toContainText('2023-12-25T00:00:00');
  await expect(datetimeListsTyped).toContainText('2024-01-01T00:00:00');
  await expect(datetimeListsTyped.locator('td').filter({ hasText: 'deadlines' })).toBeVisible();
  await expect(datetimeListsTyped).toContainText('2024-06-30T23:59:59');

  //
  // mixed struct with all types
  //

  // Table 11: mixed struct - with key/value headers
  const mixedStructTable = tables.nth(11);
  await expect(mixedStructTable.locator('th').nth(0)).toContainText('key');
  await expect(mixedStructTable.locator('th').nth(1)).toContainText('value');
  await expect(mixedStructTable.locator('td').filter({ hasText: 'name' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: 'Product A' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: 'quantity' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: '42' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: 'in_stock' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: 'true' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: 'price' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: '99.95' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: 'launch_date' })).toBeVisible();
  await expect(mixedStructTable.locator('td').filter({ hasText: '2024-01-15T10:00:00' })).toBeVisible();

  //
  // list of structs
  //

  // Table 12: basic types table - with column headers
  const listStructsBasicTypesTable = tables.nth(12);
  await expect(listStructsBasicTypesTable.locator('th').filter({ hasText: 'Color' })).toBeVisible();
  await expect(listStructsBasicTypesTable.locator('th').filter({ hasText: 'Amount' })).toBeVisible();
  await expect(listStructsBasicTypesTable.locator('th').filter({ hasText: 'In Stock' })).toBeVisible();
  const basicTypeRows = listStructsBasicTypesTable.locator('tbody tr');
  await expect(basicTypeRows).toHaveCount(3);
  await expect(basicTypeRows.nth(0).locator('td').nth(0)).toContainText('red');
  await expect(basicTypeRows.nth(0).locator('td').nth(1)).toContainText('10');
  await expect(basicTypeRows.nth(0).locator('td').nth(2)).toContainText('true');
  await expect(basicTypeRows.nth(1).locator('td').nth(0)).toContainText('green');
  await expect(basicTypeRows.nth(1).locator('td').nth(1)).toContainText('20');
  await expect(basicTypeRows.nth(1).locator('td').nth(2)).toContainText('false');
  await expect(basicTypeRows.nth(2).locator('td').nth(0)).toContainText('blue');
  await expect(basicTypeRows.nth(2).locator('td').nth(1)).toContainText('20');
  await expect(basicTypeRows.nth(2).locator('td').nth(2)).toContainText('true');

  // Table 13: float/datetime table - with column headers
  const floatDatetimeListTable = tables.nth(13);
  await expect(floatDatetimeListTable.locator('th').filter({ hasText: 'Product' })).toBeVisible();
  await expect(floatDatetimeListTable.locator('th').filter({ hasText: 'Price' })).toBeVisible();
  await expect(floatDatetimeListTable.locator('th').filter({ hasText: 'Weight' })).toBeVisible();
  await expect(floatDatetimeListTable.locator('th').filter({ hasText: 'Date Added' })).toBeVisible();
  const floatDateRows = floatDatetimeListTable.locator('tbody tr');
  await expect(floatDateRows).toHaveCount(3);
  await expect(floatDateRows.nth(0).locator('td').nth(0)).toContainText('Widget A');
  await expect(floatDateRows.nth(0).locator('td').nth(1)).toContainText('19.99');
  await expect(floatDateRows.nth(0).locator('td').nth(2)).toContainText('1.5');
  await expect(floatDateRows.nth(0).locator('td').nth(3)).toContainText('2024-01-10T08:00:00');
  await expect(floatDateRows.nth(1).locator('td').nth(0)).toContainText('Widget B');
  await expect(floatDateRows.nth(1).locator('td').nth(1)).toContainText('29.99');
  await expect(floatDateRows.nth(1).locator('td').nth(2)).toContainText('2.75');
  await expect(floatDateRows.nth(1).locator('td').nth(3)).toContainText('2024-02-15T10:30:00');
  await expect(floatDateRows.nth(2).locator('td').nth(0)).toContainText('Widget C');
  await expect(floatDateRows.nth(2).locator('td').nth(1)).toContainText('39.9'); // add(20.0, 19.99) renders as 39.989999999999995 due to JS float precision
  await expect(floatDateRows.nth(2).locator('td').nth(2)).toContainText('2.5'); // div(10.0, 4.0) = 2.5

  // Table 14: list-type columns table - with column headers
  const listTypeColumnsTable = tables.nth(14);
  await expect(listTypeColumnsTable.locator('th').filter({ hasText: 'Item' })).toBeVisible();
  await expect(listTypeColumnsTable.locator('th').filter({ hasText: 'Tags' })).toBeVisible();
  await expect(listTypeColumnsTable.locator('th').filter({ hasText: 'Scores' })).toBeVisible();
  await expect(listTypeColumnsTable.locator('th').filter({ hasText: 'Flags' })).toBeVisible();
  const listTypeRows = listTypeColumnsTable.locator('tbody tr');
  await expect(listTypeRows).toHaveCount(3);
  await expect(listTypeRows.nth(0).locator('td').nth(0)).toContainText('Item 1');
  await expect(listTypeRows.nth(0).locator('td').nth(1)).toContainText('new');
  await expect(listTypeRows.nth(0).locator('td').nth(1)).toContainText('featured');
  await expect(listTypeRows.nth(0).locator('td').nth(2)).toContainText('90');
  await expect(listTypeRows.nth(1).locator('td').nth(0)).toContainText('Item 2');
  await expect(listTypeRows.nth(1).locator('td').nth(1)).toContainText('sale');
  await expect(listTypeRows.nth(1).locator('td').nth(1)).toContainText('limited');
  await expect(listTypeRows.nth(1).locator('td').nth(2)).toContainText('88');
  await expect(listTypeRows.nth(2).locator('td').nth(0)).toContainText('Item 3');
  await expect(listTypeRows.nth(2).locator('td').nth(2)).toContainText('75');

  // Table 15: table without headers (uses columns, not headers)
  const noHeadersTable = tables.nth(15);
  await expect(noHeadersTable.locator('th')).toHaveCount(0);
  const noHeaderRows = noHeadersTable.locator('tbody tr');
  await expect(noHeaderRows).toHaveCount(2);
  await expect(noHeaderRows.nth(0).locator('td').nth(0)).toContainText('Arbitrary informtion');
  await expect(noHeaderRows.nth(0).locator('td').nth(1)).toContainText('More arbitrary information');
  await expect(noHeaderRows.nth(1).locator('td').nth(0)).toContainText('Space astronaughts are cool');
  await expect(noHeaderRows.nth(1).locator('td').nth(2)).toContainText('I like turtles');
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
  
  const priceInput = page.locator('input[data-form-field$=":price"]');
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
  const supplierIdInput = page.getByPlaceholder('Enter inventory.supplier ID');
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
  await expect(page.locator('table').filter({ hasText: 'organic' })).toBeVisible();
  
  // Verify the remove button is visible
  await expect(page.getByRole('button', { name: 'X' }).first()).toBeVisible();
  
  // Test adding another tag using Enter key
  await tagsInput.fill('eco-friendly');
  await tagsInput.press('Enter');
  
  // Verify both tags are displayed
  await expect(page.locator('table').filter({ hasText: 'organic' })).toBeVisible();
  await expect(page.locator('table').filter({ hasText: 'eco-friendly' })).toBeVisible();
  
  // Test removing a tag
  await page.getByRole('button', { name: 'X' }).first().click();
  
  // Verify one tag was removed (eco-friendly should still be there)
  await expect(page.locator('table').filter({ hasText: 'eco-friendly' })).toBeVisible();
  
  // Click submit button - this logs to console
  await page.getByRole('button', { name: 'Submit' }).click();
});

test('test - float input allows typing decimal point', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/forms.json');

  // Single float field: verify that a decimal value with '.' is accepted (type="text" input)
  const priceInput = page.locator('input[data-form-field$=":price"]');
  await priceInput.fill('3.7');
  await expect(priceInput).toHaveValue('3.7');

  // List float field: type a value with a decimal point and add it
  const floatListInput = page.getByPlaceholder('Enter number');
  await floatListInput.fill('1.5');
  await expect(floatListInput).toHaveValue('1.5');

  await page.getByRole('button', { name: 'Add' }).nth(2).click();
  await expect(page.locator('table').filter({ hasText: 'prices history' })).toContainText('1.5');
});


test('test - forms required enum and datetime fields', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/forms-required-fields.json');

  await expect(page.locator('h1')).toContainText('Forms Required Fields');

  const categorySelect = page.locator('table select').first();
  await expect(categorySelect).toHaveValue('');

  const releaseDateInput = page.locator('input[type="datetime-local"]').first();
  await expect(releaseDateInput).toHaveValue('');

  let requestCount = 0;
  page.on('request', request => {
    if (request.url().includes('/api/should-not-be-called')) {
      requestCount += 1;
    }
  });

  await page.getByRole('button', { name: 'Submit' }).click();

  await expect(page.locator('.field-error')).toHaveCount(2);
  await expect(page.locator('.field-error').first()).toContainText('(required field)');
  await expect.poll(() => requestCount).toBe(0);

  await categorySelect.selectOption('electronics');
  await releaseDateInput.fill('2026-04-16T04:25');
  await page.getByRole('button', { name: 'Submit' }).click();

  await expect.poll(() => requestCount).toBe(1);
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

test('test - viewer gallery page', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/viewer-gallery.json');

  // Check heading
  await expect(page.locator('h1')).toContainText('Gallery Viewer');

  // Gallery controls should be visible
  const prevButton = page.getByRole('button', { name: '◀' });
  const nextButton = page.getByRole('button', { name: '▶' });
  await expect(prevButton).toBeVisible();
  await expect(nextButton).toBeVisible();

  // Initial state: first image (1 / 3), prev disabled, next enabled
  await expect(page.locator('.viewer-controls span')).toContainText('1 / 3');
  await expect(prevButton).toBeDisabled();
  await expect(nextButton).toBeEnabled();

  // Navigate to second image
  await nextButton.click();
  await expect(page.locator('.viewer-controls span')).toContainText('2 / 3');
  await expect(prevButton).toBeEnabled();
  await expect(nextButton).toBeEnabled();

  // Navigate to third (last) image
  await nextButton.click();
  await expect(page.locator('.viewer-controls span')).toContainText('3 / 3');
  await expect(prevButton).toBeEnabled();
  await expect(nextButton).toBeDisabled();

  // Navigate back to second image
  await prevButton.click();
  await expect(page.locator('.viewer-controls span')).toContainText('2 / 3');
  await expect(prevButton).toBeEnabled();
  await expect(nextButton).toBeEnabled();
});

test('test - secure field redaction', async ({ page }) => {
  const fakeToken = 'test_access_token_value_abc123xyz_very_long';

  // Mock the login API endpoint
  await page.route('**/api/auth/login-user', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        result: {
          access_token: fakeToken,
          token_type: 'bearer'
        }
      })
    });
  });

  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/test-secure-fields.json');

  // Confirm the login form is shown with a password input
  await expect(page.locator('input[type="password"]')).toBeVisible();

  // Fill in the form and submit
  await page.locator('input[type="text"]').fill('test@example.com');
  await page.getByRole('button', { name: 'Submit' }).click();

  // Wait for result
  await expect(page.locator('#lingo-app')).toContainText('success');

  // Confirm access_token is redacted
  await expect(page.locator('#lingo-app')).toContainText('REDACTED');
  await expect(page.locator('#lingo-app')).not.toContainText(fakeToken);

  // Press show button for access_token (last 'show' button, after the form's password show button)
  await page.getByRole('button', { name: 'show' }).last().click();

  // Confirm access_token is not redacted
  await expect(page.locator('#lingo-app')).not.toContainText('REDACTED');
  await expect(page.locator('#lingo-app')).toContainText(fakeToken);

  // Confirm password input is still visible in the form (auth/login-user form)
  await expect(page.locator('input[type="password"]')).toBeVisible();

  // Click show sensitive fields for the password input
  await page.getByRole('button', { name: 'show' }).first().click();

  // Confirm there are no password inputs
  await expect(page.locator('input[type="password"]')).not.toBeVisible();
});
test('test - spec file loaded from url query param', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/?spec=data/lingo/pages/test-page.json');

  await expect(page.locator('#spec-select')).toHaveValue('data/lingo/pages/test-page.json');
  await expect(page.locator('h1')).toContainText('Example document');
  await expect(page.locator('#lingo-app')).toContainText('Please tell us your name:');
});

test('test - spec file added to url on dropdown change', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000/');

  await page.locator('#spec-select').selectOption('data/lingo/pages/test-page.json');

  await expect(page).toHaveURL(/[?&]spec=data%2Flingo%2Fpages%2Ftest-page\.json/);
  await expect(page.locator('h1')).toContainText('Example document');
});

test('test - timers', async ({ page }) => {
  test.setTimeout(25000); // timers test needs extra time for countdown to complete

  await page.goto('http://127.0.0.1:8000/');
  await page.locator('#spec-select').selectOption('data/lingo/pages/timers.json');

  await expect(page.locator('h1')).toContainText('Timers');

  // Auto-start: clock should be running - capture the time text and wait for it to change
  const initialTime = await page.locator('#lingo-app').textContent();
  await page.waitForTimeout(1500);
  const updatedTime = await page.locator('#lingo-app').textContent();
  expect(updatedTime).not.toEqual(initialTime);

  // Initial countdown state is -1, button should be enabled
  await expect(page.locator('#lingo-app')).toContainText('-1');
  await expect(page.getByRole('button', { name: 'start countdown' })).toBeEnabled();

  // Start the countdown from the button
  await page.getByRole('button', { name: 'start countdown' }).click();

  // -1 should disappear and countdown should start at 5
  await expect(page.locator('#lingo-app')).not.toContainText('Countdown: -1');
  await expect(page.locator('#lingo-app')).toContainText('5');

  // Button should now be disabled since countdown is running
  await expect(page.getByRole('button', { name: 'start countdown' })).toBeDisabled();

  // Wait for the countdown to finish (it runs from 5 down to -1, 6 seconds max + buffer)
  await expect(page.locator('#lingo-app')).toContainText('Countdown: -1', { timeout: 9000 });

  // Timer has disabled itself - button should be enabled again
  await expect(page.getByRole('button', { name: 'start countdown' })).toBeEnabled();
});
