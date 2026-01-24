import { test } from './fixtures.js';
import { expect } from '@playwright/test';

//
// helper functions
//

async function fillOpParamField(page, paramName, param, value) {
  const paramType = param.type;
  const elementType = param.element_type;
  
  const pattern = new RegExp('^' + param.name.lower_case + '', 'i');

  // Handle list types
  if (paramType === 'list') {
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
      } else if (param.enum) {
        await row.locator('select.list-input').selectOption(String(val));
      }else if (elementType === 'datetime') {
        await row.locator('input.list-input[type="datetime-local"]').fill(String(val).substring(0, 16));
      } else {
        await row.locator('input.list-input').fill(String(val));
      }
      
      // Click the Add button to add this value to the list
      await row.getByRole('button', { name: 'Add' }).click();
    }
  } else if (paramType === 'bool') {
    // For boolean fields, use checkbox
    const checkbox = page.getByRole('row', { name: pattern })
      .locator('input[type="checkbox"]');
    if (value) {
      await checkbox.check();
    } else {
      await checkbox.uncheck();
    }
  } else if (param.enum) {
    // For enum fields, use select dropdown
    await page.getByRole('row', { name: pattern })
      .locator('select')
      .selectOption(String(value));
  } else if (paramType === 'int') {
    // For int fields, use input[type="number"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="number"]')
      .fill(String(value));
  } else if (paramType === 'float') {
    // For float fields, use input[type="number"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="number"]')
      .fill(String(value));
  } else if (paramType === 'datetime') {
    // For datetime fields, use input[type="datetime-local"]
    await page.getByRole('row', { name: pattern })
      .locator('input[type="datetime-local"]')
      .fill(String(value).substring(0, 16));
  } else if (paramType === 'foreign_key') {
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

async function clearAllListParams(page, op) {
  for (const [paramName, param] of Object.entries(op.params || {})) {
    if (param.type === 'list') {
      // Find the row for this param
      const row = page.getByRole('row', { name: new RegExp(param.name.lower_case, 'i') });
      // Find all X/remove buttons in this row (one per list item)
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

//
// op test
//

test('test ops for all modules', async ({ browser, crudEnv, crudSession }) => {
  const context = await browser.newContext({ storageState: crudSession.storageState });
  const page = await context.newPage();
  const { host, spec } = crudEnv;
  
  // Navigate to index page
  await page.goto(host);
  await expect(page.locator('h1')).toContainText('::');

  // Iterate over each module
  for (const [moduleName, module] of Object.entries(spec.modules)) {
    const moduleKebab = module.name.kebab_case;
    
    // Skip auth module
    if (moduleKebab === 'auth') {
      continue;
    }
    
    // Click module link
    await page.getByRole('link', { name: moduleKebab }).click();
    await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);

    // Iterate over each op in the module
    for (const [opName, op] of Object.entries(module.ops || {})) {
      const opKebab = op.name.kebab_case;
      
      // Skip hidden ops
      if (op.hidden === true) {
        continue;
      }

      // Click op link
      await page.getByRole('link', { name: opKebab }).click();
      await expect(page.locator('h1')).toContainText(`:: ${opKebab}`);

      // Iterate over each test case defined in the op's tests.test_cases
      const testCases = op.tests?.test_cases || [];
      
      for (const testCase of testCases) {
        // Clear any list params from previous test case
        await clearAllListParams(page, op);
        
        // Update form to match test case's params
        for (const [paramName, value] of Object.entries(testCase.params || {})) {
          if (op.params && op.params[paramName]) {
            await fillOpParamField(page, paramName, op.params[paramName], value);
          }
        }

        // Click submit button
        await page.getByRole('button', { name: 'Submit' }).click();
        
        // Confirm result matches result defined in test case
        const expectedResult = testCase.expected_result;
        
        // Wait for result to appear
        await page.waitForLoadState('networkidle');
        
        // Check that the result is displayed in the page
        if (expectedResult !== null && expectedResult !== undefined) {
          // Convert result to string for comparison
          const resultStr = typeof expectedResult === 'object' 
            ? JSON.stringify(expectedResult) 
            : String(expectedResult);
          await expect(page.locator('#lingo-app')).toContainText(resultStr);
        }
      }

      // Click breadcrumb to go back to module page
      await page.getByRole('link', { name: moduleKebab }).click();
      await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);
    }

    // Click breadcrumb to go back to index page
    await page.getByRole('link', { name: spec.project.name.lower_case }).click();
    await expect(page.locator('h1')).toContainText('::');
  }
});
