import { test, expect } from '@playwright/test';

// vars :: {"template_app":"project.name.snake_case", "http://localhost:5005": "client.default_host"}
// vars :: {"template-module": "module.name.kebab_case", "template module": "module.name.lower_case"}
// vars :: {"single model": "model.name.lower_case", "single-model": "model.name.kebab_case", "single_model": "model.name.snake_case"}

test('test - template module - single model - pagination', async ({ page }) => {
  await page.goto('http://localhost:5005/');

  await expect(page.locator('h1')).toContainText('template_app');
  await page.getByRole('link', { name: 'template module' }).last().click();

  await expect(page.locator('h1')).toContainText('template module');
  await page.getByRole('link', { name: 'single model' }).click();
  await expect(page.getByRole('heading')).toContainText('single model');

  // vars :: {"['id', 'single_bool', 'single_int', 'single_float', 'single_string', 'single_enum', 'single_datetime']": "macro.html_field_list(model.fields)"}
  const fields = ['id', 'single_bool', 'single_int', 'single_float', 'single_string', 'single_enum', 'single_datetime'];
  for (const field of fields) {
    await expect(page.locator('th', {hasText: field}).first()).toBeVisible();
  }

  // await page.getByRole('button', { name: '>>>' }).click();
  // await page.getByRole('button', { name: '<<<' }).click();
  await page.getByRole('button', { name: 'refresh' }).click();
});


test('test - template module - single model - instance', async ({ page }) => {

    const textToContain = []

    // create item

    await page.goto('http://localhost:5005/template-module/single-model');
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
    // end macro ::
    
    await page.getByRole('button', { name: 'submit' }).click();

    await expect(page.locator('#create-single-model-status')).toContainText('success');

    const createdItem = await page.locator('#created-single-model');
    const createdItemId = await createdItem.innerText();
    textToContain.push(createdItemId);
    
    await createdItem.click();

    for (const text of textToContain) {
        await expect(page.locator('#single-model-read-tbody')).toContainText(text);
    }

    await page.getByRole('button', { name: 'edit' }).click();
    await page.getByRole('button', { name: 'save' }).click();
    await page.getByRole('link', { name: createdItemId }).click();
    
    await page.getByRole('button', { name: 'delete' }).click();
    await page.getByRole('button', { name: 'no, cancel' }).click();
    await page.getByRole('link', { name: 'single_model' }).click();
    
    await page.getByPlaceholder('single model id').click();
    await page.getByPlaceholder('single model id').fill(createdItemId);
    await page.getByRole('button', { name: 'get' }).click();

    for (const text of textToContain) {
        await expect(page.locator('#single-model-read-tbody')).toContainText(text);
    }

    await page.getByRole('button', { name: 'delete' }).click();
    await page.getByRole('button', { name: 'yes, please delete' }).click();
    await expect(page.locator('#single-model-not-found')).toContainText('item not found');
});

test('test - template module - single model - create random', async ({ page }) => {
  await page.goto('http://localhost:5005/template-module/single-model/create');
  
  await page.getByRole('button', { name: 'random' }).click();
  await page.getByRole('button', { name: 'submit' }).click();

  await expect(page.locator('#create-single-model-status')).toBeVisible();
  await expect(page.locator('#create-single-model-status')).toContainText('success');
});