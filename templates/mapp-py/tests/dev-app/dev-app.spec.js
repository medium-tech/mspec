import { test, createAndLoginUser } from '../fixtures.js';
import { expect } from '@playwright/test';

test('edit form state - single choice fields', async ({ browser, crudEnv }) => {

	/* 
		Check edit form state
			- ensure that editing triggers the (modified inicator)
			- ensure that canceling reverts the form to the original values
	*/

	// init page
	const context = await browser.newContext({ });
	const page = await context.newPage();
	await context.addCookies([{ name: 'protocol_mode', value: 'true', domain: new URL(crudEnv.host).hostname, path: '/' }]);

	// navigate to model
	await page.goto(crudEnv.host);
	await page.getByRole('link', { name: 'model-type-tests' }).click();
	await page.getByRole('link', { name: 'single-choice-fields' }).click();
	
	// fill out model form
	await page.getByRole('row', { name: 'x bool:' }).getByRole('checkbox').uncheck();
	await page.getByRole('row', { name: 'x int:' }).getByRole('spinbutton').fill('123456');
	await page.getByRole('row', { name: 'x float:' }).getByRole('textbox').fill('1.23456');
	await page.getByRole('row', { name: 'x string:' }).getByRole('textbox').fill('hello.string');
	await page.getByRole('row', { name: 'x enum:' }).getByRole('combobox').selectOption('taco');
	await page.getByRole('row', { name: 'x datetime:' }).getByRole('textbox').fill('1999-01-15T03:42');

	// submit and navigate to item view
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('success');
	await page.getByRole('link', { name: 'view item' }).click();

	// confirm values are correct
	const checkModelData = async () => {
		await expect(page.getByRole('row', { name: 'x_bool' })).toContainText('false');
		await expect(page.getByRole('row', { name: 'x_int' })).toContainText('123456');
		await expect(page.getByRole('row', { name: 'x_float' })).toContainText('1.23456');
		await expect(page.getByRole('row', { name: 'x_string' })).toContainText('hello.string');
		await expect(page.getByRole('row', { name: 'x_enum' })).toContainText('taco');
		await expect(page.getByRole('row', { name: 'x_datetime' })).toContainText('1999-01-15T03:42:00');
	};

	checkModelData();

	// edit x bool
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await page.getByRole('checkbox').check();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_bool' })).not.toContainText('true');
	checkModelData();

	// edit x int
	await page.getByRole('button', { name: 'edit' }).click();
	await page.getByRole('spinbutton').fill('363');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_int' })).not.toContainText('363');
	checkModelData();

	// edit x float
	await page.getByRole('button', { name: 'edit' }).click();
	await page.getByRole('row', { name: 'x float:' }).getByRole('textbox').fill('123456.7');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_float' })).not.toContainText('123456.7');
	checkModelData();

	// edit x string
	await page.getByRole('button', { name: 'edit' }).click();
	await page.getByRole('row', { name: 'x string:' }).getByRole('textbox').fill('hello.updated.string');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_string' })).not.toContainText('hello.updated.string');
	checkModelData();

	// edit x enum
	await page.getByRole('button', { name: 'edit' }).click();
	await page.getByRole('row', { name: 'x enum:' }).getByRole('combobox').selectOption('tlayuda');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_enum' })).not.toContainText('tlayuda');
	checkModelData();

	// edit x datetime
	await page.getByRole('button', { name: 'edit' }).click();
	await page.getByRole('row', { name: 'x datetime:' }).getByRole('textbox').fill('1999-01-15T04:42');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();

	await expect(page.getByRole('row', { name: 'x_datetime' })).not.toContainText('1999-01-15T04:42');
	checkModelData();

	// reload data and confirm values are correct
	await page.getByRole('button', { name: 'load' }).click();
	checkModelData();
});