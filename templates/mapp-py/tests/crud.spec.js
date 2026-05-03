import { test, createAndLoginUser } from './fixtures.js';
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

function getUniqueExampleFromModel(model, index = 0) {

  if (!model.hasOwnProperty('fields')) {
    throw new Error(`Model "${model.name.pascal_case}" has no fields defined`);
  }

  const timestamp = Date.now();
  const data = {};

  for (const [fieldName, field] of Object.entries(model.fields)) {
    if (!field.hasOwnProperty('examples')) {
      throw new Error(`Field "${fieldName}" in model "${model.name.pascal_case}" has no examples defined`);
    }
    const value = field.examples[index];
    data[fieldName] = (field.unique === true && field.type === 'str') ? `${value}-${timestamp}` : value;
  }
  return data;
}

async function checkViewField(page, fieldName, field, value) {

  // Skip user_id field as it's set automatically
  if (fieldName === 'user_id') return;

  const fieldType = field.type;
  const elementType = field.element_type;
  const refs = field.references;

  // Skip auth FK references
  if (refs && refs.module === 'auth') return;

  // Scope element searches to the row for this field in the view table
  const fieldRow = page.getByRole('row', { name: new RegExp('^' + fieldName) });

  if (fieldType === 'list' && elementType === 'foreign_key') {
    if (!refs) return;
    const table = refs.table;
    if (!Array.isArray(value) || value.length === 0) return;

    if (table === 'file') {
      // File IDs are dynamically assigned by the server, so we can't use example values.
      // Verify at least one download button is present and trigger a download via the first one.
      const downloadButtons = fieldRow.getByRole('button', { name: /^⬇/ });
      await expect(downloadButtons.first()).toBeVisible();
      const downloadPromise = page.waitForEvent('download');
      await downloadButtons.first().click();
      await downloadPromise;
    } else if (table === 'image' || table === 'master_image') {
      // Verify gallery viewer is present with navigation controls
      await expect(fieldRow.locator('.viewer-container')).toBeVisible();
      await expect(fieldRow.getByRole('button', { name: '◀' })).toBeVisible();
      await expect(fieldRow.getByRole('button', { name: '▶' })).toBeVisible();
      // Navigate through the gallery (we always add 2 images so nav buttons are enabled)
      await fieldRow.getByRole('button', { name: '▶' }).click();
      await fieldRow.getByRole('button', { name: '◀' }).click();
    } else {
      // Non-file FK list: find all "go to" links actually rendered in the row
      const links = fieldRow.getByRole('link', { name: /^go to / });
      await expect(links.first()).toBeVisible();
      for (const link of await links.all()) {
        await link.click();
        await expect(page.locator('#lingo-app')).toContainText('id');
        await page.goBack();
        await expect(page.locator('#lingo-app')).toContainText('id');
      }
    }

  } else if (fieldType === 'foreign_key') {
    if (!refs) return;
    const table = refs.table;
    const refField = refs.field;
    const refModule = refs.module.replaceAll('_', '-');
    const refTable = table.replaceAll('_', '-');

    if (String(value) === '-1') {
      // Default placeholder value
      await expect(fieldRow).toContainText('-1 indicates no id was set');
    } else if (table === 'file' && refField === 'id') {
      // Click download file button and verify download starts
      const downloadPromise = page.waitForEvent('download');
      await fieldRow.getByRole('button', { name: 'download file' }).click();
      await downloadPromise;
    } else if ((table === 'image' || table === 'master_image') && refField === 'id') {
      // Verify viewer is present
      await expect(fieldRow.locator('.viewer-container')).toBeVisible();
      // Download button becomes enabled once image loads (Playwright auto-retries)
      const downloadPromise = page.waitForEvent('download');
      await fieldRow.getByRole('button', { name: '⬇' }).click();
      await downloadPromise;
      // Open viewer popup by clicking the popup button
      await fieldRow.getByRole('button', { name: '⌞ ⌝' }).click();
      // Close the popup
      await fieldRow.getByRole('button', { name: '×' }).click();
    } else {
      // Non-file FK: verify link is present and takes you to the correct page
      const loc = `${refModule}/${refTable}/${value}`;
      await expect(fieldRow.getByRole('link', { name: `go to ${loc}` })).toBeVisible();
      await fieldRow.getByRole('link', { name: `go to ${loc}` }).click();
      await expect(page.locator('#lingo-app')).toContainText('id');
      await page.goBack();
      await expect(page.locator('#lingo-app')).toContainText('id');
    }

  } else if (fieldType === 'datetime') {
    // Datetime is stored as YYYY-MM-DDTHH:MM:SS; check first 16 chars to match input
    await expect(page.locator('#lingo-app')).toContainText(String(value).substring(0, 16));

  } else if (fieldType === 'list') {
    if (Array.isArray(value) && value.length > 0) {
      if (elementType === 'datetime') {
        // Each list datetime element displayed as YYYY-MM-DDTHH:MM:SS
        for (const v of value) {
          await expect(page.locator('#lingo-app')).toContainText(String(v).substring(0, 16));
        }
      } else {
        // Other list types displayed as ", " joined string
        await expect(page.locator('#lingo-app')).toContainText(value.join(', '));
      }
    }

  } else {
    // Primitive fields: bool, int, float, str, enum
    await expect(page.locator('#lingo-app')).toContainText(String(value));
  }
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
        // File-based FK list: upload one file per example value so the list has the right count
        const sampleFile = getSampleFileForRef(refs);
        const count = Math.max(Array.isArray(value) ? value.length : 0, 1);
        for (let i = 0; i < count; i++) {
          await row.locator('input[type="file"]').setInputFiles(sampleFile);
          await expect(row.locator('button.remove-button')).toHaveCount(i + 1);
        }
      } else if (refs) {
        // Non-file FK list: use the popup to find and select pre-seeded records
        const values = Array.isArray(value) ? value : [];
        for (let i = 0; i < Math.max(values.length, 1); i++) {
          await row.getByRole('button', { name: `Find ${refs.table}` }).click();
          await page.locator('.popup-content > div > table > tbody > tr').nth(i).click();
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
    // For float fields, use input[type="text"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="text"]')
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
      await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
      await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');
      await expect(page.locator('#lingo-app')).not.toContainText('error');
    } else if (refs && String(value) !== '-1') {
      // Non-file FK with non-default value: use the popup to find a pre-seeded record
      const row = page.getByRole('row', { name: pattern });
      await row.getByRole('button', { name: `Find ${refs.table}` }).click();

      // wait for page not to have text 'pending'
      await expect(page.locator('#lingo-app')).not.toContainText('pending');

      await page.locator('.popup-content > div > table > tbody > tr').first().click();
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

  // set protocol_mode=true as cookie

  await context.addCookies([{ name: 'protocol_mode', value: 'true', domain: new URL(crudEnv.host).hostname, path: '/' }]);

  //
  // pre-seed CRUD tests
  //

  await page.goto(crudEnv.host);
  await expect(page.locator('h1')).toContainText('::');

  // Pre-seed records for non-file FK popup selections
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

        // Create 2 pre-seeded records so that list FK fields can select 2 distinct items
        for (let seedNum = 0; seedNum < 2; seedNum++) {
          // Navigate to create a pre-seeded record for this referenced model
          await page.goto(crudEnv.host);
          await page.getByRole('link', { name: refSpecModule.name.kebab_case, exact: true }).click();
          await page.getByRole('link', { name: refSpecModel.name.kebab_case, exact: true }).click();

          // Fill form with example data (preSeedMode=true skips FK fields to avoid cycles)
          const seedExample = getExampleFromModel(refSpecModel, 0);
          for (const [fn, val] of Object.entries(seedExample)) {
            await fillFormField(page, fn, refSpecModel.fields[fn], val, true);
          }

          await page.getByRole('button', { name: 'Submit' }).click();
          await expect(page.locator('#lingo-app')).toContainText('Success');
        }

        preSeeded.add(seedKey);
      }
    }
  }

  //
  // main CRUD tests
  // 

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
      await page.getByRole('link', { name: modelKebab, exact: true }).click();
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

      // Verify that the created data is displayed correctly for each field
      for (const [fieldName, value] of Object.entries(createExample)) {
        await checkViewField(page, fieldName, model.fields[fieldName], value);
      }

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
      await page.getByRole('button', { name: 'load', exact: true }).click();
      
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
      await page.getByRole('link', { name: moduleKebab, exact: true }).click();
      await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);
    }

    // Click breadcrumb back to index
    await page.getByRole('link', { name: crudEnv.spec.project.name.lower_case, exact: true }).click();
    await expect(page.locator('h1')).toContainText('::');
  }
});


test('test validation errors are displayed in form', async ({ browser, crudEnv, crudSession }) => {
  const context = await browser.newContext({ storageState: crudSession.storageState });
  const page = await context.newPage();

  await context.addCookies([{ name: 'protocol_mode', value: 'true', domain: new URL(crudEnv.host).hostname, path: '/' }]);

  // Find the first module and model that we can navigate to
  const modules = crudEnv.spec.modules;
  let targetModel, targetModuleKebab, targetModelKebab;
  for (const [moduleName, module] of Object.entries(modules)) {
    if (['auth', 'file-system', 'media'].includes(module.name.kebab_case)) continue;
    for (const [modelName, model] of Object.entries(module.models || {})) {
      if (model.hidden === true) continue;
      if (model.auth && model.auth.max_models_per_user !== -1) continue;
      targetModel = model;
      targetModuleKebab = module.name.kebab_case;
      targetModelKebab = model.name.kebab_case;
      break;
    }
    if (targetModel) break;
  }

  expect(targetModel).toBeDefined();

  // Navigate to the model create page
  await page.goto(crudEnv.host);
  await page.getByRole('link', { name: targetModuleKebab, exact: true }).click();
  await page.getByRole('link', { name: targetModelKebab, exact: true }).click();
  await expect(page.locator('h1')).toContainText(`:: ${targetModelKebab}`);

  //
  // Part 1: test validation errors on the create form
  //

  const apiUrl = `${crudEnv.host}/api/${targetModuleKebab}/${targetModelKebab}`;
  const fieldErrorMessage = 'This field failed validation';
  const firstFieldName = Object.keys(targetModel.fields)[0];

  // Mock POST to return a VALIDATION_ERROR
  await page.route(apiUrl, async route => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'This model has failed validation',
            field_errors: {
              [firstFieldName]: fieldErrorMessage
            }
          }
        })
      });
    } else {
      await route.continue();
    }
  });

  // fill form (it needs to be valid to pass client side validation to trigger mocked server validation error)
  const createExample = getExampleFromModel(targetModel, 0);
  for (const [fieldName, value] of Object.entries(createExample)) {
    await fillFormField(page, fieldName, targetModel.fields[fieldName], value);
  }

  // Click submit to trigger the mocked validation error
  await page.getByRole('button', { name: 'Submit' }).click();

  // Verify the validation error message is shown in the status area
  await expect(page.locator('#lingo-app')).toContainText('This model has failed validation');

  // Verify the field error message is shown in the form's third column
  const createFieldError = page.locator('.field-error');
  await expect(createFieldError).toBeVisible();
  await expect(createFieldError).toContainText(fieldErrorMessage);

  // Unroute the mock so subsequent requests go through normally
  await page.unroute(apiUrl);

  //
  // Part 2: create an actual item then test validation errors on the edit form
  //

  // form is already filled, now that we've removed the mock, submit should succeed and create an item we can edit
  await page.getByRole('button', { name: 'Submit' }).click();
  await expect(page.locator('#lingo-app')).toContainText('Success');

  // Follow link to the newly created item
  await page.getByRole('link', { name: 'view item' }).click();
  await expect(page.locator('h1')).toContainText(`:: ${targetModelKebab}`);

  // Extract the item ID from the current page URL
  const itemUrl = page.url();
  const itemId = itemUrl.split('/').pop();
  const itemApiUrl = `${crudEnv.host}/api/${targetModuleKebab}/${targetModelKebab}/${itemId}`;

  // Load the item and enter edit mode
  await page.getByRole('button', { name: 'load', exact: true }).click();
  await expect(page.locator('#lingo-app')).toContainText('loaded');
  await page.getByRole('button', { name: 'edit', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();

  // Mock PUT to return a VALIDATION_ERROR
  const editFieldErrorMessage = 'This field failed validation during edit';
  await page.route(itemApiUrl, async route => {
    if (route.request().method() === 'PUT') {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'This model has failed validation',
            field_errors: {
              [firstFieldName]: editFieldErrorMessage
            }
          }
        })
      });
    } else {
      await route.continue();
    }
  });

  // Submit the edit form to trigger the mocked validation error
  await page.getByRole('button', { name: 'Submit' }).click();

  // Verify the validation error message is shown in the status area
  await expect(page.locator('#lingo-app')).toContainText('This model has failed validation');

  // Verify the edit form is still visible (not reverted to view mode)
  await expect(page.getByRole('button', { name: 'Submit' })).toBeVisible();

  // Verify the field error message is shown in the form's third column
  const editFieldError = page.locator('.field-error');
  await expect(editFieldError).toBeVisible();
  await expect(editFieldError).toContainText(editFieldErrorMessage);

  // Verify the cancel button is enabled so user can exit edit mode
  await expect(page.getByRole('button', { name: 'cancel', exact: true })).toBeEnabled();

  // Click cancel - field errors should clear and form should disappear
  await page.getByRole('button', { name: 'cancel', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Submit' })).not.toBeVisible();
  await expect(page.locator('.field-error')).not.toBeVisible();
});


test('test non-owner does not see edit or delete buttons', async ({ browser, crudEnv }) => {

  // find a model with require_login:true so it has user-ownership
  const modules = crudEnv.spec.modules;
  let targetModel, targetModuleKebab, targetModelKebab;
  for (const [_moduleName, module] of Object.entries(modules)) {
    if (['auth', 'file-system', 'media'].includes(module.name.kebab_case)) continue;
    for (const [_modelName, model] of Object.entries(module.models || {})) {
      if (model.hidden === true) continue;
      if (!model.auth || !model.auth.require_login) continue;
      if (model.auth.max_models_per_user === 0) continue;
      targetModel = model;
      targetModuleKebab = module.name.kebab_case;
      targetModelKebab = model.name.kebab_case;
      break;
    }
    if (targetModel) break;
  }
  expect(targetModel).toBeDefined();

  // create and log in as user A (the owner)
  const userA = await createAndLoginUser(crudEnv.host, browser, 'owner');
  const contextA = await browser.newContext({ storageState: userA.storageState });
  const pageA = await contextA.newPage();
  await contextA.addCookies([{ name: 'protocol_mode', value: 'true', domain: new URL(crudEnv.host).hostname, path: '/' }]);

  // create a model instance as user A
  await pageA.goto(crudEnv.host);
  await pageA.getByRole('link', { name: targetModuleKebab, exact: true }).click();
  await pageA.getByRole('link', { name: targetModelKebab, exact: true }).click();

  const createExample = getUniqueExampleFromModel(targetModel, 0);
  for (const [fieldName, value] of Object.entries(createExample)) {
    await fillFormField(pageA, fieldName, targetModel.fields[fieldName], value);
  }
  await pageA.getByRole('button', { name: 'Submit' }).click();
  await expect(pageA.locator('#lingo-app')).toContainText('Success');

  // navigate to the new item and capture its URL
  await pageA.getByRole('link', { name: 'view item' }).click();
  await expect(pageA.locator('h1')).toContainText(`:: ${targetModelKebab}`);
  const itemUrl = pageA.url();

  // load the item and confirm owner sees edit and delete buttons
  await pageA.getByRole('button', { name: 'load', exact: true }).click();
  await expect(pageA.locator('#lingo-app')).toContainText('loaded');
  await expect(pageA.getByRole('button', { name: 'edit', exact: true })).toBeVisible();
  await expect(pageA.getByRole('button', { name: 'delete', exact: true })).toBeVisible();

  await contextA.close();

  // create and log in as user B (non-owner)
  const userB = await createAndLoginUser(crudEnv.host, browser, 'non-owner');
  const contextB = await browser.newContext({ storageState: userB.storageState });
  const pageB = await contextB.newPage();
  await contextB.addCookies([{ name: 'protocol_mode', value: 'true', domain: new URL(crudEnv.host).hostname, path: '/' }]);

  // navigate directly to the item created by user A
  await pageB.goto(itemUrl);
  await pageB.getByRole('button', { name: 'load', exact: true }).click();
  await expect(pageB.locator('#lingo-app')).toContainText('loaded');

  // non-owner should not see edit or delete buttons
  await expect(pageB.getByRole('button', { name: 'edit', exact: true })).not.toBeVisible();
  await expect(pageB.getByRole('button', { name: 'delete', exact: true })).not.toBeVisible();

  await contextB.close();
});
