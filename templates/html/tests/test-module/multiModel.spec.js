import { test, expect } from '@playwright/test';

// vars :: {"unit_test":"project.name.snake_case", "http://localhost:5005": "client.default_host"}
// vars :: {"test-module": "module.name.kebab_case", "test module": "module.name.lower_case"}
// vars :: {"multi model": "model.name.lower_case", "multi-model": "model.name.kebab_case", "multi_model": "model.name.snake_case"}

test('test - test module - multi model - pagination', async ({ page }) => {
  await page.goto('http://localhost:5005/');

  await expect(page.locator('h1')).toContainText('unit_test');
  await page.getByRole('link', { name: 'test module' }).last().click();

  await expect(page.locator('h1')).toContainText('test module');
  await page.getByRole('link', { name: 'multi model' }).click();
  await expect(page.getByRole('heading')).toContainText('multi model');

  // vars :: {"['id', 'single_bool', 'single_int', 'single_float', 'single_string', 'single_enum', 'single_datetime', 'multi_bool', 'multi_int', 'multi_float', 'multi_string']": "macro.html_field_list(model.fields)"}
  const fields = ['id', 'single_bool', 'single_int', 'single_float', 'single_string', 'single_enum', 'single_datetime', 'multi_bool', 'multi_int', 'multi_float', 'multi_string'];
  for (const field of fields) {
    await expect(page.locator('th', {hasText: field}).first()).toBeVisible();
  }

  // await page.getByRole('button', { name: '>>>' }).click();
  // await page.getByRole('button', { name: '<<<' }).click();
  await page.getByRole('button', { name: 'refresh' }).click();
});


test('test - test module - multi model - instance', async ({ page }) => {

    const textToContain = []

    // create item

    await page.goto('http://localhost:5005/test-module/multi-model');
    await page.getByRole('button', { name: 'create' }).click();
    
    // insert :: macro.html_unittest_form(model.fields)
    // macro :: html_unittest_form_bool :: {"single_bool": "field", "__ignored__": "value"}
    // single_bool
    await page.locator('input[name="single_bool"]').check();
    textToContain.push('yes');

    // macro :: html_unittest_form_int :: {"single_int": "field", "55": "value"}
    // single_int
    await page.locator('input[name="single_int"]').fill('55');
    textToContain.push('55');

    // macro :: html_unittest_form_float :: {"single_float": "field", "3.33": "value"}
    // single_float
    await page.locator('input[name="single_float"]').fill('3.33');
    textToContain.push('3.33');

    // macro :: html_unittest_form_str :: {"single_string": "field", "this is a unittest": "value"}
    // single_string
    await page.locator('input[name="single_string"]').click();
    await page.locator('input[name="single_string"]').fill('this is a unittest');
    textToContain.push('this is a unittest');

    // macro :: html_unittest_form_str_enum :: {"single_enum": "field", "red": "value"}
    // single_enum
    await page.locator('select[name="single_enum"]').selectOption('red');
    textToContain.push('red');

    // macro :: html_unittest_form_datetime :: {"single_datetime": "field", "2020-03-02T05:15": "value"}
    // single_datetime
    await page.locator('input[name="single_datetime"]').click();
    await page.locator('input[name="single_datetime"]').fill('2020-03-02T05:15');

    // macro :: html_unittest_form_list_bool :: {"multi_bool": "field", "true": "list_element_1", "false": "list_element_2"}
    // multi_bool
    await page.locator('input[name="multi_bool"]').click();
    await page.locator('input[name="multi_bool"]').fill('true');
    await page.locator('input[name="multi_bool"]').press('Enter');
    await page.locator('input[name="multi_bool"]').fill('false');
    await page.locator('input[name="multi_bool"]').press('Enter');
    textToContain.push('true, false');

    // macro :: html_unittest_form_list_int :: {"multi_int": "field", "1": "list_element_1", "2": "list_element_2"}
    // multi_int
    await page.locator('input[name="multi_int"]').click();
    await page.locator('input[name="multi_int"]').fill('1');
    await page.locator('input[name="multi_int"]').press('Enter');
    await page.locator('input[name="multi_int"]').fill('2');
    await page.locator('input[name="multi_int"]').press('Enter');
    textToContain.push('1, 2');

    // macro :: html_unittest_form_list_float :: {"multi_float": "field", "1.4": "list_element_1", "2.34578": "list_element_2"}
    // multi_float
    await page.locator('input[name="multi_float"]').click();
    await page.locator('input[name="multi_float"]').fill('1.4');
    await page.locator('input[name="multi_float"]').press('Enter');
    await page.locator('input[name="multi_float"]').fill('2.34578');
    await page.locator('input[name="multi_float"]').press('Enter');
    textToContain.push('1.4, 2.34578');

    // macro :: html_unittest_form_list_str :: {"multi_string": "field", "one": "list_element_1", "two": "list_element_2"}
    // multi_string
    await page.locator('input[name="multi_string"]').click();
    await page.locator('input[name="multi_string"]').fill('one');
    await page.locator('input[name="multi_string"]').press('Enter');
    await page.locator('input[name="multi_string"]').fill('two');
    await page.locator('input[name="multi_string"]').press('Enter');
    textToContain.push('one, two');

    // macro :: html_unittest_form_list_str_enum :: {"multi_enum": "field", "zebra": "list_element_1", "giraffe": "list_element_2"}
    // multi_enum
    await page.locator('select[name="multi_enum"]').selectOption('zebra');
    await page.locator('select[name="multi_enum"]').selectOption('giraffe');
    textToContain.push('zebra, giraffe');

    // macro :: html_unittest_form_list_datetime :: {"multi_datetime": "field", "2020-03-02T05:15": "list_element_1", "2022-11-22T12:45": "list_element_2"}
    // multi_datetime
    await page.locator('input[name="multi_datetime"]').click();
    await page.locator('input[name="multi_datetime"]').fill('2020-03-02T05:15');
    await page.getByRole('button', { name: 'add' }).click();
    await page.locator('input[name="multi_datetime"]').fill('2022-11-22T12:45');
    await page.getByRole('button', { name: 'add' }).click();
    // end macro ::

    await page.getByRole('button', { name: 'submit' }).click();

    await expect(page.locator('#create-multi-model-status')).toContainText('success');

    const createdItem = await page.locator('#created-multi-model');
    const createdItemId = await createdItem.innerText();
    textToContain.push(createdItemId);
    
    await createdItem.click();

    for (const text of textToContain) {
        await expect(page.locator('#multi-model-read-tbody')).toContainText(text);
    }

    await page.getByRole('button', { name: 'edit' }).click();
    await page.getByRole('button', { name: 'save' }).click();
    await page.getByRole('link', { name: createdItemId }).click();
    
    await page.getByRole('button', { name: 'delete' }).click();
    await page.getByRole('button', { name: 'no, cancel' }).click();
    await page.getByRole('link', { name: 'multi_model' }).click();

    await page.getByPlaceholder('multi model id').click();
    await page.getByPlaceholder('multi model id').fill(createdItemId);
    await page.getByRole('button', { name: 'get' }).click();

    for (const text of textToContain) {
        await expect(page.locator('#multi-model-read-tbody')).toContainText(text);
    }

    await page.getByRole('button', { name: 'delete' }).click();
    await page.getByRole('button', { name: 'yes, please delete' }).click();
    await expect(page.locator('#multi-model-not-found')).toContainText('item not found');
});

test('test - test module - multi model - create random', async ({ page }) => {
  await page.goto('http://localhost:5005/test-module/multi-model/create');

  await page.getByRole('button', { name: 'random' }).click();
  await page.getByRole('button', { name: 'submit' }).click();

  await expect(page.locator('#create-multi-model-status')).toBeVisible();
  await expect(page.locator('#create-multi-model-status')).toContainText('success');
});