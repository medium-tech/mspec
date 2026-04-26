import { test } from './fixtures.js';
import { expect } from '@playwright/test';

//
// workflow test
//

test('test user workflow', async ({ browser, crudEnv }) => {
	const context = await browser.newContext();
	const page = await context.newPage();

	await page.goto(crudEnv.host);

	//
	// front page
	//

	// confirm front page has custom content
	await expect(page.getByRole('heading')).toContainText('medium tech');
	await expect(page.locator('span')).toContainText('-->');
	// confirm front page does not have protocol_mode content
	await expect(page.locator('#lingo-app')).not.toContainText(':: sosh net');
	await expect(page.locator('#lingo-app')).not.toContainText(':: available modules');

	//
	// sosh net main page
	//

	await page.getByRole('link', { name: 'enter sosh net' }).click();
	await expect(page.locator('h1')).toContainText('shosh net');
	await expect(page.getByRole('link', { name: 'mtech' })).toBeVisible();
	await expect(page.getByRole('link', { name: 'sosh-net' })).toBeVisible();
	await expect(page.locator('h2')).toContainText(':: the network');
	await expect(page.getByRole('link', { name: 'front page' })).toBeVisible();
	await expect(page.getByRole('link', { name: 'profiles' })).toBeVisible();
	await expect(page.getByRole('link', { name: 'forums' })).toBeVisible();
	await expect(page.getByRole('link', { name: 'account' })).toBeVisible();
	await expect(page.locator('#lingo-app')).toContainText('this is sosh net.');
	await page.getByRole('link', { name: 'account' }).click();


});

