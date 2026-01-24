import { test } from './fixtures.js';
import { expect } from '@playwright/test';


test('test pagination UI navigation', async ({ browser, paginationEnv, paginationSession }) => {
  const context = await browser.newContext({ storageState: paginationSession.storageState });
  const page = await context.newPage();
  const { host, spec } = paginationEnv;

  // Load index page for pagination env
  await page.goto(host);
  await expect(page.locator('#lingo-app')).toContainText(':: available modules');

  const pageSize = 5;
  const totalItems = 25;
  const expectedPages = totalItems / pageSize; // 5 pages

  // Iterate over each module
  for (const module of Object.values(spec.modules)) {
    const moduleKebab = module.name.kebab_case;
    
    // Click link with module name (kebab case)
    await page.getByRole('link', { name: moduleKebab }).click();
    await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);

    // Iterate over each model in module
    for (const model of Object.values(module.models)) {
      // Skip if hidden
      if (model.hidden) {
        continue;
      }

      // Skip if max_models_per_user is 0 (no data allowed)
      if (model.auth && model.auth.max_models_per_user === 0) {
        continue;
      }

      const modelKebab = model.name.kebab_case;

      // Click link on module page with model name (kebab case)
      await page.getByRole('link', { name: modelKebab }).click();
      await expect(page.locator('h1')).toContainText(`:: ${modelKebab}`);

      // Ensure there are 5 items displayed in list
      // Wait for the table to be visible
      const firstTbody = page.locator('tbody').first();
      await firstTbody.waitFor({ state: 'visible' });
      let rows = firstTbody.locator('tr');
      const initialRowCount = await rows.count();
      expect(initialRowCount).toBe(pageSize);

      // Click next button 4 times (visit all 5 pages, confirming 25 total items)
      let totalItemsVisited = initialRowCount;
      
      for (let i = 0; i < expectedPages - 1; i++) {
        // Click the next button
        const nextButton = page.getByRole('button', { name: 'next' });
        await expect(nextButton).toBeVisible();
        await nextButton.click();
        
        // Wait for the data to load by waiting for network idle or table update
        await page.waitForLoadState('networkidle');
        
        // Re-query rows after navigation to get fresh count
        rows = firstTbody.locator('tr');
        const pageRows = await rows.count();
        totalItemsVisited += pageRows;
        
        // Each page should have pageSize items except possibly the last
        expect(pageRows).toBeLessThanOrEqual(pageSize);
        expect(pageRows).toBeGreaterThan(0);
      }

      // Verify we've seen all 25 items
      expect(totalItemsVisited).toBe(totalItems);

      // Click prev button until at first page
      for (let i = 0; i < expectedPages - 1; i++) {
        const prevButton = page.getByRole('button', { name: 'prev' });
        await expect(prevButton).toBeVisible();
        await prevButton.click();
        
        // Wait for the data to load
        await page.waitForLoadState('networkidle');
      }

      // Verify we're back at the first page by checking we have 5 items again
      rows = firstTbody.locator('tr');
      const finalRows = await rows.count();
      expect(finalRows).toBe(pageSize);

      // Click breadcrumb to go back to module page
      await page.getByRole('link', { name: moduleKebab }).click();
      await expect(page.locator('h1')).toContainText(`:: ${moduleKebab}`);
    }

    // Click breadcrumb to go back to index page
    await page.getByRole('link', { name: spec.project.name.lower_case }).click();
    await expect(page.locator('#lingo-app')).toContainText(':: available modules');
  }
});