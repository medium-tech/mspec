import { test } from './fixtures.js';
import { expect } from '@playwright/test';

test('confirm test setup', async ({ crudEnv, paginationEnv }) => {
  expect(crudEnv.spec).toEqual(paginationEnv.spec);
  expect(crudEnv.host).not.toEqual(paginationEnv.host);
});

test('test hidden entry points', async ({ browser, crudEnv }) => {

	const { host: crudHost } = crudEnv;

	// init //
	const context = await browser.newContext();
	const page = await context.newPage();
	await page.goto(crudHost);
	await context.addCookies([{ 
		name: 'protocol_mode', 
		value: 'true', 
		path: '/',
		domain: new URL(crudHost).hostname,
		secure: false,
	}]);
	await page.reload();
	await page.goto(crudHost);

	//
	// auth
	//

	await page.getByRole('link', { name: 'auth' }).click();
  	await expect(page.locator('#lingo-app')).not.toContainText('drop-sessions');

	let response = await page.goto(`${crudHost}/auth/drop-sessions`);
	expect(response.status()).toBe(404);
  	await expect(page.locator('pre')).toContainText('{"code": "NOT_FOUND", "message": "not found: /auth/drop-sessions"}');

	//
	// com
	//

	await page.goto(crudHost);

	await page.getByRole('link', { name: 'com' }).click();
  	await expect(page.locator('#lingo-app')).not.toContainText('send-email');

	response = await page.goto(`${crudHost}/com/send-email`);
	expect(response.status()).toBe(404);
  	await expect(page.locator('pre')).toContainText('{"code": "NOT_FOUND", "message": "not found: /com/send-email"}');

});