import { test } from './fixtures.js';
import { expect } from '@playwright/test';

test('crud root returns 200', async ({ browser, crudEnv, crudSession }) => {
  const context = await browser.newContext({ storageState: crudSession.storageState });
  const page = await context.newPage();
  
  const response = await page.goto(crudEnv.host);
  expect(response.status()).toBe(200);
});

//
// helper functions
//

function getExampleFromModel(model, index = 0) {
  const data = {};
  for (const [fieldName, field] of Object.entries(model.fields || {})) {
    if (!field.examples || !field.examples[index]) {
      throw new Error(`No example for field "${model.name.pascal_case}.${fieldName}" at index ${index}`);
    }
    data[fieldName] = field.examples[index];
  }
  return data;
}

async function fillFormField(page, fieldName, field, value) {
  const fieldType = field.type;
  const elementType = field.element_type;
  
  // Skip user_id field as it's set automatically
  if (fieldName === 'user_id') {
    return;
  }

  // Handle list types
  if (fieldType === 'list') {
    // For list fields, we need to fill them as comma-separated values in a textarea
    const valueStr = Array.isArray(value) ? value.join(', ') : String(value);
    await page.getByRole('row', { name: new RegExp(field.name.lower_case, 'i') })
      .locator('textarea')
      .fill(valueStr);
  } else if (fieldType === 'bool') {
    // For boolean fields, use checkbox
    const checkbox = page.getByRole('row', { name: new RegExp(field.name.lower_case, 'i') })
      .locator('input[type="checkbox"]');
    if (value) {
      await checkbox.check();
    } else {
      await checkbox.uncheck();
    }
  } else if (field.enum) {
    // For enum fields, use select dropdown
    await page.getByRole('row', { name: new RegExp(field.name.lower_case, 'i') })
      .locator('select')
      .selectOption(String(value));
  } else {
    // For other fields (str, int, float, datetime), use textbox
    await page.getByRole('row', { name: new RegExp(field.name.lower_case, 'i') })
      .getByRole('textbox')
      .fill(String(value));
  }
}

//
// crud test
//

test('test crud operations on all models', async ({ browser, crudEnv, crudSession }) => {
  const context = await browser.newContext({ storageState: crudSession.storageState });
  const page = await context.newPage();
  
  // Navigate to index page
  await page.goto(crudEnv.host);
  await expect(page.locator('h1')).toContainText('::');

  // Iterate over each module
  for (const [moduleName, module] of Object.entries(crudEnv.spec.modules)) {
    const moduleKebab = module.name.kebab_case;
    
    // Click module link
    await page.getByRole('link', { name: moduleKebab }).click();
    await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);

    // Iterate over each model in the module
    for (const [modelName, model] of Object.entries(module.models || {})) {
      const modelKebab = model.name.kebab_case;
      
      // Skip hidden models
      if (model.hidden === true) {
        continue;
      }

      // Skip models with max_models_per_user = 0 (can't create any)
      if (model.auth && model.auth.max_models_per_user === 0) {
        continue;
      }

      // Click model link
      await page.getByRole('link', { name: modelKebab }).click();
      await expect(page.locator('h1')).toContainText(`:: ${modelKebab}`);

      // Get example data for create (index 0)
      const createExample = getExampleFromModel(model, 0);
      
      // Fill out create form
      for (const [fieldName, value] of Object.entries(createExample)) {
        await fillFormField(page, fieldName, model.fields[fieldName], value);
      }

      // Submit create form
      await page.getByRole('button', { name: 'Submit' }).click();
      
      // Ensure success message
      await expect(page.locator('#lingo-app')).toContainText('success:');

      // Extract the created item ID from the success message
      // The success message typically contains the id
      const successText = await page.locator('#lingo-app').textContent();
      const idMatch = successText.match(/id['":\s]+(\d+)/i);
      
      if (!idMatch) {
        throw new Error(`Could not extract ID from success message: ${successText}`);
      }
      
      const createdId = idMatch[1];

      // Follow link to new item (read operation)
      await page.getByRole('link', { name: createdId }).click();
      
      // Confirm it loads successfully
      await expect(page.locator('h1')).toContainText(`:: ${modelKebab}`);
      await expect(page.locator('#lingo-app')).toContainText('id');

      // Click edit button to update model
      await page.getByRole('button', { name: 'Edit' }).click();
      
      // Get example data for update (index 1)
      let updateExample;
      try {
        updateExample = getExampleFromModel(model, 1);
      } catch (e) {
        // If no second example, use first example again
        updateExample = createExample;
      }

      // Fill out edit form with updated values
      for (const [fieldName, value] of Object.entries(updateExample)) {
        await fillFormField(page, fieldName, model.fields[fieldName], value);
      }

      // Press submit button to save
      await page.getByRole('button', { name: 'Submit' }).click();
      
      // Wait for update to complete
      await expect(page.locator('#lingo-app')).toContainText('success:');

      // Click load to re-load data from server
      await page.getByRole('button', { name: 'Load' }).click();
      
      // Confirm data was edited - check that we can see the updated values
      for (const [fieldName, value] of Object.entries(updateExample)) {
        if (fieldName !== 'user_id') {
          // The page should contain the updated value somewhere
          await expect(page.locator('#lingo-app')).toContainText(String(value));
        }
      }

      // Click delete button
      await page.getByRole('button', { name: 'Delete' }).click();
      
      // Click confirm delete button
      await page.getByRole('button', { name: 'Confirm Delete' }).click();
      
      // Confirm success message
      await expect(page.locator('#lingo-app')).toContainText('success:');

      // Reload page, ensure error (item should no longer exist)
      await page.reload();
      await expect(page.locator('#lingo-app')).toContainText('error:');

      // Click breadcrumb back to module
      await page.getByRole('link', { name: moduleKebab }).click();
      await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);
    }

    // Click breadcrumb back to index
    await page.getByRole('link', { name: crudEnv.spec.project.name.kebab_case }).click();
    await expect(page.locator('h1')).toContainText('::');
  }
});
