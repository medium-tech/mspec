import { test, expect } from '@playwright/test';

// vars :: {"mspec":"project.name.snake_case", "http://localhost:9009": "client.default_host"}
// vars :: {"sample-module": "module.name.kebab_case", "sample module": "module.name.lower_case", "sample_module": "module.name.snake_case"}
// vars :: {"example item": "model.name.lower_case", "example-item": "model.name.kebab_case", "example_item": "model.name.snake_case"}

test('test - sample module - example item - pagination', async ({ page }) => {
  await page.goto('http://localhost:9009/');

  await expect(page.locator('h1')).toContainText('mspec');
  await page.getByRole('link', { name: 'sample_module' }).click();
  await expect(page.locator('h1')).toContainText('sample module');
  await page.getByRole('link', { name: 'example_item' }).click();
  await expect(page.getByRole('heading')).toContainText('example item');

  await page.getByRole('button', { name: '>>>' }).click();
  await page.getByRole('button', { name: '<<<' }).click();
  await page.getByRole('button', { name: 'refresh' }).click();
});


test('test - sample module - example item - instance', async ({ page }) => {

    const textToContain = []

    // create item

    await page.goto('http://localhost:9009/sample-module/example-item');
    await page.getByRole('button', { name: 'create' }).click();

    // macro :: html_unittest_form_str :: {"description": "field"}
    await page.locator('input[name="description"]').click();
    await page.locator('input[name="description"]').fill('this is a unittest');
    textToContain.push('this is a unittest');


    // macro :: html_unittest_form_bool :: {"verified": "field"}
    await page.locator('input[name="verified"]').check();
    textToContain.push('yes');

    // macro :: html_unittest_form_enum :: {"color": "field", "green": "enum_choice"}
    await page.locator('select[name="color"]').selectOption('green');
    textToContain.push('green');

    // macro :: html_unittest_form_int :: {"count": "field"}
    await page.locator('input[name="count"]').fill('55');
    textToContain.push('55');

    // macro :: html_unittest_form_float :: {"score": "field"}
    await page.locator('input[name="score"]').fill('3.33');
    textToContain.push('3.33');

    // macro :: html_unittest_form_list :: {"tags": "field"}
    await page.locator('html').click();
    await page.locator('input[name="tags"]').click();
    await page.locator('input[name="tags"]').fill('one');
    await page.locator('input[name="tags"]').press('Enter');
    await page.locator('input[name="tags"]').fill('two');
    await page.locator('input[name="tags"]').press('Enter');
    textToContain.push('one, two');
    // end macro ::

    // insert :: macro.html_unittest_form(model.fields)
    
    await page.getByRole('button', { name: 'submit' }).click();

    await expect(page.locator('#create-example-item-status')).toContainText('success');

    const createdItem = await page.locator('#created-example-item');
    const createdItemId = await createdItem.innerText();
    textToContain.push(createdItemId);
    
    await createdItem.click();

    for (const text of textToContain) {
        await expect(page.locator('#example-item-read-tbody')).toContainText(text);
    }

    await page.getByRole('button', { name: 'edit' }).click();
    await page.getByRole('button', { name: 'save' }).click();
    await page.getByRole('link', { name: createdItemId }).click();
    
    await page.getByRole('button', { name: 'delete' }).click();
    await page.getByRole('button', { name: 'no, cancel' }).click();
    await page.getByRole('link', { name: 'example_item' }).click();
    
    await page.getByPlaceholder('example item id').click();
    await page.getByPlaceholder('example item id').fill(createdItemId);
    await page.getByRole('button', { name: 'get' }).click();

    for (const text of textToContain) {
        await expect(page.locator('#example-item-read-tbody')).toContainText(text);
    }

    await page.getByRole('button', { name: 'delete' }).click();
    await page.getByRole('button', { name: 'yes, please delete' }).click();
    await expect(page.locator('#example-item-not-found')).toContainText('item not found');
});
