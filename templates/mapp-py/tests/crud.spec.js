import { test } from './fixtures.js';
import { expect } from '@playwright/test';

//
// helper functions
//

const FILE_TABLE_REFS = ['file', 'image', 'master_image'];

function isFileFkRef(references) {
  return references && FILE_TABLE_REFS.includes(references.table);
}

function getSampleFileForRef(references) {
  if (references.module === 'file_system' && references.table === 'file') {
    return './tests/samples/lorem-document.pdf';
  }
  return './tests/samples/splash-low.jpg';
}

async function clearAllListFields(page, model) {
  for (const [fieldName, field] of Object.entries(model.fields)) {
    if (field.type === 'list') {
      // Find the row for this field
      const row = page.getByRole('row', { name: new RegExp(field.name.lower_case, 'i') });
      // Find all X/remove buttons in this row (one per list item)
      // The remove buttons are assumed to have role 'button' and name 'X'
      let removeButtons = await row.locator('button.remove-button').all();
      // Keep removing until there are no more
      while (removeButtons.length > 0) {
        await removeButtons[0].click();
        // Re-query after each removal, as the DOM updates
        removeButtons = await row.locator('button.remove-button').all();
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

async function fillFormField(page, fieldName, field, value, preSeedMode = false) {
  const fieldType = field.type;
  const elementType = field.element_type;
  const refs = field.references;

  // Skip user_id field as it's set automatically
  if (fieldName === 'user_id') {
    return;
  }

  // Skip auth FK references
  if (refs && refs.module === 'auth') {
    return;
  }

  const pattern = new RegExp('^' + field.name.lower_case, 'i')

  // Handle list types
  if (fieldType === 'list') {
    if (elementType === 'foreign_key') {
      // Skip FK list fields in pre-seed mode to avoid cycles
      if (preSeedMode) return;

      const row = page.getByRole('row', { name: pattern });

      if (isFileFkRef(refs)) {
        // File-based FK list: upload a sample file to add one item
        const sampleFile = getSampleFileForRef(refs);
        await row.locator('input[type="file"]').setInputFiles(sampleFile);
        await expect(row.locator('button.remove-button')).toHaveCount(1);
      } else if (refs) {
        // Non-file FK list: use the popup to find and select a pre-seeded record
        const values = Array.isArray(value) ? value : [];
        for (let i = 0; i < Math.max(values.length, 1); i++) {
          await row.getByRole('button', { name: `Find ${refs.table}` }).click();
          await page.locator('.popup-content > table > tbody > tr').first().click();
          await expect(row.locator('button.remove-button')).toHaveCount(i + 1);
        }
      }
      return;
    }
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
    // Skip FK fields in pre-seed mode to avoid cycles
    if (preSeedMode) return;

    if (isFileFkRef(refs)) {
      // File-based FK: upload a sample file
      const sampleFile = getSampleFileForRef(refs);
      const row = page.getByRole('row', { name: pattern });
      await row.locator('input[type="file"]').setInputFiles(sampleFile);
      await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');
    } else if (refs && String(value) !== '-1') {
      // Non-file FK with non-default value: use the popup to find a pre-seeded record
      const row = page.getByRole('row', { name: pattern });
      await row.getByRole('button', { name: `Find ${refs.table}` }).click();
      await page.locator('.popup-content > table > tbody > tr').first().click();
    }
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

test('test crud and list for all models', async ({ browser, crudEnv, crudSession, skipModules }) => {
  const context = await browser.newContext({ storageState: crudSession.storageState });
  const page = await context.newPage();
  
  // Navigate to index page
  await page.goto(crudEnv.host);
  await expect(page.locator('h1')).toContainText('::');

  // Pre-seed records for non-file FK popup selections.
  // These records persist throughout the test since the main CRUD loop only
  // deletes records it creates, not the ones created here.
  const preSeeded = new Set();
  for (const [moduleName, module] of Object.entries(crudEnv.spec.modules)) {
    const moduleKebab = module.name.kebab_case;
    if (skipModules.includes(moduleKebab)) continue;

    for (const [modelName, model] of Object.entries(module.models || {})) {
      if (model.hidden === true) continue;
      if (model.auth && model.auth.max_models_per_user === 0) continue;

      for (const [fieldName, field] of Object.entries(model.fields || {})) {
        const refs = field.references;
        if (!refs || refs.module === 'auth' || refs.table === 'user') continue;
        if (isFileFkRef(refs)) continue;

        const isFkField = field.type === 'foreign_key';
        const isListFkField = field.type === 'list' && field.element_type === 'foreign_key';
        if (!isFkField && !isListFkField) continue;

        // Only pre-seed if the field has a non-default example (will actually use popup)
        const examples = field.examples || [];
        const hasNonDefaultExample = examples.some(ex => {
          if (Array.isArray(ex)) return ex.length > 0;
          return String(ex) !== '-1' && ex !== null && ex !== undefined;
        });
        if (!hasNonDefaultExample) continue;

        const seedKey = `${refs.module}.${refs.table}`;
        if (preSeeded.has(seedKey)) continue;

        // Find the referenced module and model in the spec
        const refSpecModule = crudEnv.spec.modules[refs.module];
        if (!refSpecModule) continue;
        const refSpecModel = refSpecModule.models[refs.table];
        if (!refSpecModel) continue;

        // Navigate to create a pre-seeded record for this referenced model
        await page.goto(crudEnv.host);
        await page.getByRole('link', { name: refSpecModule.name.kebab_case }).click();
        await page.getByRole('link', { name: refSpecModel.name.kebab_case }).click();

        // Fill form with example data (preSeedMode=true skips FK fields to avoid cycles)
        const seedExample = getExampleFromModel(refSpecModel, 0);
        for (const [fn, val] of Object.entries(seedExample)) {
          await fillFormField(page, fn, refSpecModel.fields[fn], val, true);
        }

        await page.getByRole('button', { name: 'Submit' }).click();
        await expect(page.locator('#lingo-app')).toContainText('Success');

        preSeeded.add(seedKey);
      }
    }
  }

  // Navigate back to index before starting main CRUD loop
  await page.goto(crudEnv.host);
  await expect(page.locator('h1')).toContainText('::');

  // Iterate over each module
  for (const [moduleName, module] of Object.entries(crudEnv.spec.modules)) {
    const moduleKebab = module.name.kebab_case;
    
  // Skip built-in modules
    if (skipModules.includes(moduleKebab)) {
      continue;
    }

    // Click module link
    await page.getByRole('link', { name: moduleKebab }).click();
    await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);

    // Iterate over each model in the module
    for (const [modelName, model] of Object.entries(module.models || {})) {
      const modelKebab = model.name.kebab_case;
      
      // Skip hidden models
      if (model.hidden === true) {
        continue
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
          const fieldDef = model.fields[fieldName];

          // Skip FK fields - values are dynamic IDs from file uploads or popup selections
          if (fieldDef.type === 'foreign_key') {
            continue;
          }

          // if value is a list expect it to be joined on ", "
          if (Array.isArray(value)) {
            if (fieldDef.element_type === 'foreign_key') {
              // FK list fields - values are dynamic IDs, skip exact check
              continue;
            }
            await expect(page.locator('#lingo-app')).toContainText(value.join(', '));
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
