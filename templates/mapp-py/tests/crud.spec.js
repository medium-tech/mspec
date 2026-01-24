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

async function clearAllListFields(page, model) {
  console.log(`Clearing all list fields for model ${model.name.pascal_case}`);
  for (const [fieldName, field] of Object.entries(model.fields)) {
    if (field.type === 'list') {
      // Find the row for this field
      const row = page.getByRole('row', { name: new RegExp(field.name.lower_case, 'i') });
      console.log(`Clearing list field: ${fieldName}`, typeof row);
      // Find all X/remove buttons in this row (one per list item)
      // The remove buttons are assumed to have role 'button' and name 'X'
      let removeButtons = await row.locator('button.remove-button').all();
      console.log(`Found ${removeButtons.length} items to remove in field ${fieldName}`, typeof removeButtons);
      // Keep removing until there are no more
      while (removeButtons.length > 0) {
        await removeButtons[0].click();
        console.log(`Removed one item from field ${fieldName}`);
        // Re-query after each removal, as the DOM updates
        removeButtons = await row.locator('button.remove-button').all();
        console.log(`Remaining items to remove in field ${fieldName}: ${removeButtons.length}`);
      }
    }
  }
}

function getExampleFromModel(model, index = 0) {

  if(!model.hasOwnProperty('fields')) {
    throw new Error(`Model "${model.name.pascal_case}" has no fields defined`);
  }

  const data = {};
  
  for (const [fieldName, field] of Object.entries(model.fields)) {
    if (!field.hasOwnProperty('examples')) {
      throw new Error(`Field "${fieldName}" in model "${model.name.pascal_case}" has no examples defined`);
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

  const pattern = new RegExp('^' + field.name.lower_case + '', 'i')

  // Handle list types
  if (fieldType === 'list') {
    // For list fields, we need to add each value individually using the Add button
    const values = Array.isArray(value) ? value : [value];
    const row = page.getByRole('row', { name: pattern });
    
    for (const val of values) {
      // Fill the list input based on element type
      if (elementType === 'bool') {
        const checkbox = row.locator('input.list-input[type="checkbox"]');
        if (val) {
          await checkbox.check();
        } else {
          await checkbox.uncheck();
        }
      } else if (field.enum) {
        await row.locator('select.list-input').selectOption(String(val));
      }else if (elementType === 'datetime') {
        await row.locator('input.list-input[type="datetime-local"]').fill(String(val).substring(0, 16));
      } else {
        await row.locator('input.list-input').fill(String(val));
      }
      
      // Click the Add button to add this value to the list
      await row.getByRole('button', { name: 'Add' }).click();
    }
  } else if (fieldType === 'bool') {
    // For boolean fields, use checkbox
    const checkbox = page.getByRole('row', { name: pattern })
      .locator('input[type="checkbox"]');
    if (value) {
      await checkbox.check();
    } else {
      await checkbox.uncheck();
    }
  } else if (field.enum) {
    // For enum fields, use select dropdown
    await page.getByRole('row', { name: pattern })
      .locator('select')
      .selectOption(String(value));
  } else if (fieldType === 'int') {
    // For int fields, use input[type="number"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="number"]')
      .fill(String(value));
  } else if (fieldType === 'float') {
    // For float fields, use input[type="number"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="number"]')
      .fill(String(value));
  } else if (fieldType === 'datetime') {
    // For datetime fields, use input[type="datetime-local"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="datetime-local"]')
      .fill(String(value).substring(0, 16));
  } else if (fieldType === 'foreign_key') {
    // For foreign_key fields, use input[type="text"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="text"]')
      .fill(String(value));
  } else {
    // For str and fallback, use input[type="text"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="text"]')
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
      await expect(page.locator('#lingo-app')).toContainText('Success');

      // Follow link to new item (read operation)
      await page.getByRole('link', { name: 'view item' }).click();
      
      // Confirm it loads successfully
      await expect(page.locator('h1')).toContainText(`:: ${modelKebab}`);
      await expect(page.locator('#lingo-app')).toContainText('id');

      // Click edit button to update model
      await page.getByRole('button', { name: 'edit' }).click();

      await clearAllListFields(page, model);
      
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
      await expect(page.locator('#lingo-app')).toContainText('edited');

      // Click load to re-load data from server
      await page.getByRole('button', { name: 'load' }).click();
      
      // Confirm data was edited - check that we can see the updated values
      for (const [fieldName, value] of Object.entries(updateExample)) {
        if (fieldName !== 'user_id') {
          // The page should contain the updated value somewhere

          // if value is a list expect it to be joined on ", "
          if(Array.isArray(value)) {
            await expect(page.locator('#lingo-app')).toContainText(value.join(', '));
            continue;
          }else{
            await expect(page.locator('#lingo-app')).toContainText(String(value));
          }
        }
      }

      // Click delete button
      await page.getByRole('button', { name: 'delete' }).click();
      
      // Click confirm delete button
      await page.getByRole('button', { name: 'confirm delete' }).click();
      
      // Confirm success message
      await expect(page.locator('#lingo-app')).toContainText('item deleted successfully');

      // Reload page, ensure error (item should no longer exist)
      await page.reload();
      await expect(page.locator('#lingo-app')).toContainText('error:');

      // Click breadcrumb back to module
      await page.getByRole('link', { name: moduleKebab }).click();
      await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);
    }

    // Click breadcrumb back to index
    await page.getByRole('link', { name: crudEnv.spec.project.name.lower_case }).click();
    await expect(page.locator('h1')).toContainText('::');
  }
});
