import { test, expect } from '@playwright/test';

// vars :: {"mspec":"project.name.snake_case", "http://localhost:9009": "client.default_host"}
// vars :: {"sample": "module.name.snake_case", "sample item": "model.name.lower_case", "sample-item": "model.name.kebab_case"}

test('test - sample - sample item - pagination', async ({ page }) => {
  await page.goto('http://localhost:9009/');

  await expect(page.locator('h1')).toContainText('mspec');
  await page.getByRole('link', { name: 'sample' }).click();
  await expect(page.locator('h1')).toContainText('sample');
  await page.getByRole('link', { name: 'sample-item' }).click();
  await expect(page.getByRole('heading')).toContainText('sample item');

  await page.getByRole('button', { name: '>>>' }).click();
  await page.getByRole('button', { name: '<<<' }).click();
  await page.getByRole('button', { name: 'refresh' }).click();
});


test('test - sample - sample item - instance', async ({ page }) => {

    // create item

    await page.goto('http://localhost:9009/sample/sample-item');
    await page.getByRole('button', { name: 'create' }).click();

    // macro :: html_unittest_form_str :: {"name": "field"}
    await page.locator('input[name="name"]').click();
    await page.locator('input[name="name"]').fill('this is a unittest');

    // macro :: html_unittest_form_bool :: {"verified": "field"}
    await page.locator('input[name="verified"]').check();

    // macro :: html_unittest_form_enum :: {"color": "field", "green": "enum_choice"}
    await page.locator('select[name="color"]').selectOption('green');

    // macro :: html_unittest_form_int :: {"age": "field"}
    await page.locator('input[name="age"]').click({
        clickCount: 3
    });
    await page.locator('input[name="age"]').fill('55');

    // macro :: html_unittest_form_float :: {"score": "field"}
    await page.locator('input[name="score"]').fill('3.33');

    // macro :: html_unittest_form_list :: {"tags": "field"}
    await page.locator('html').click();
    await page.locator('input[name="tags"]').click();
    await page.locator('input[name="tags"]').fill('one');
    await page.locator('input[name="tags"]').press('Enter');
    await page.locator('input[name="tags"]').fill('two');
    await page.locator('input[name="tags"]').press('Enter');
    // end macro ::

    // insert :: macro.html_unittest_form(model.fields)
    
    await page.getByRole('button', { name: 'submit' }).click();

    await expect(page.locator('#create-sample-item-status')).toContainText('success');

    const createdItem = await page.locator('#created-sample-item');
    const createdItemId = await createdItem.innerText();
    
    await createdItem.click();

    await expect(page.locator('#sample-item-read-tbody')).toContainText(createdItemId);
    await expect(page.locator('#sample-item-read-tbody')).toContainText('this is a unittest');
    await expect(page.locator('#sample-item-read-tbody')).toContainText('yes');
    await expect(page.locator('#sample-item-read-tbody')).toContainText('green');
    await expect(page.locator('#sample-item-read-tbody')).toContainText('55');
    await expect(page.locator('#sample-item-read-tbody')).toContainText('3.33');
    await expect(page.locator('#sample-item-read-tbody')).toContainText('one, two');

    await page.getByRole('button', { name: 'edit' }).click();
    await page.getByRole('checkbox').check();
    await page.locator('input[name="name"]').click();
    await page.locator('input[name="name"]').fill('modified name');
    await page.locator('html').click();
    await page.getByRole('button', { name: 'save' }).click();
    await page.getByRole('link', { name: createdItemId }).click();
    
    await expect(page.locator('#sample-item-read-tbody')).toContainText('modified name');
    await page.getByRole('button', { name: 'delete' }).click();
    await page.getByRole('button', { name: 'no, cancel' }).click();
    await page.getByRole('link', { name: 'sample_item' }).click();
    await page.getByPlaceholder('sample item id').click();
    await page.getByPlaceholder('sample item id').fill(createdItemId);
    await page.getByRole('button', { name: 'get' }).click();
    await expect(page.locator('#sample-item-read-tbody')).toContainText(createdItemId);
    await page.getByRole('button', { name: 'delete' }).click();
    await page.getByRole('button', { name: 'yes, please delete' }).click();
    await expect(page.locator('#sample-item-not-found')).toContainText('item not found');
});
