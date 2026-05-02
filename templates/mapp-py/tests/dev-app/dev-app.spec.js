import { test, createAndLoginUser } from '../fixtures.js';
import { expect } from '@playwright/test';

test('edit form state - single choice fields', async ({ browser, crudEnv }) => {

	/* 
		Check edit form state
			- ensure that editing triggers the (modified inicator)
			- ensure that canceling reverts the form to the original values
	*/

	//
	// create model
	//

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

	await checkModelData();

	//
	// test model edit form
	//

	// edit x bool
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await page.getByRole('checkbox').check();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_bool' })).not.toContainText('true');
	await checkModelData();

	// edit x int
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await page.getByRole('spinbutton').fill('363');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_int' })).not.toContainText('363');
	await checkModelData();

	// edit x float
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await page.getByRole('row', { name: 'x float:' }).getByRole('textbox').fill('123456.7');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_float' })).not.toContainText('123456.7');
	await checkModelData();

	// edit x string
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await page.getByRole('row', { name: 'x string:' }).getByRole('textbox').fill('hello.updated.string');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_string' })).not.toContainText('hello.updated.string');
	await checkModelData();

	// edit x enum
	await page.getByRole('button', { name: 'edit' }).click();
	await page.getByRole('row', { name: 'x enum:' }).getByRole('combobox').selectOption('tlayuda');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	
	await expect(page.getByRole('row', { name: 'x_enum' })).not.toContainText('tlayuda');
	await checkModelData();

	// edit x datetime
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await page.getByRole('row', { name: 'x datetime:' }).getByRole('textbox').fill('1999-01-15T04:42');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();

	await expect(page.getByRole('row', { name: 'x_datetime' })).not.toContainText('1999-01-15T04:42');
	await checkModelData();

	// reload data and confirm values are correct
	await page.getByRole('button', { name: 'load' }).click();
	await checkModelData();
});

test('edit form state - multi choice fields', async ({ browser, crudEnv }) => {

	/*
		Check edit form state for list (multi choice) fields
			- ensure that adding an item to a list triggers the (modified indicator)
			- ensure that removing the newly added item removes the (modified indicator)
			- ensure that removing an existing item triggers the (modified indicator)
			- ensure that canceling reverts the form to the original values
	*/

	// init page
	const context = await browser.newContext({ });
	const page = await context.newPage();
	await context.addCookies([{ name: 'protocol_mode', value: 'true', domain: new URL(crudEnv.host).hostname, path: '/' }]);

	//
	// create model
	//

	// navigate to model
	await page.goto(crudEnv.host);
	await page.getByRole('link', { name: 'model-type-tests' }).click();
	await page.getByRole('link', { name: 'multi-choice-fields' }).click();

	// fill out model form with first example values
	const boolRow = page.getByRole('row', { name: 'x list bool:' });
	await boolRow.locator('input.list-input[type="checkbox"]').check();
	await boolRow.getByRole('button', { name: 'Add' }).click();
	await boolRow.locator('input.list-input[type="checkbox"]').uncheck();
	await boolRow.getByRole('button', { name: 'Add' }).click();

	const intRow = page.getByRole('row', { name: 'x list int:' });
	await intRow.locator('input.list-input').fill('7');
	await intRow.getByRole('button', { name: 'Add' }).click();
	await intRow.locator('input.list-input').fill('11');
	await intRow.getByRole('button', { name: 'Add' }).click();

	const floatRow = page.getByRole('row', { name: 'x list float:' });
	await floatRow.locator('input.list-input').fill('3.14');
	await floatRow.getByRole('button', { name: 'Add' }).click();
	await floatRow.locator('input.list-input').fill('2.718');
	await floatRow.getByRole('button', { name: 'Add' }).click();

	const stringRow = page.getByRole('row', { name: 'x list string:' });
	await stringRow.locator('input.list-input').fill('banana');
	await stringRow.getByRole('button', { name: 'Add' }).click();

	const enumRow = page.getByRole('row', { name: 'x list enum:' });
	await enumRow.locator('select.list-input').selectOption('chorizo');
	await enumRow.getByRole('button', { name: 'Add' }).click();
	await enumRow.locator('select.list-input').selectOption('al pastor');
	await enumRow.getByRole('button', { name: 'Add' }).click();

	const datetimeRow = page.getByRole('row', { name: 'x list datetime:' });
	await datetimeRow.locator('input.list-input[type="datetime-local"]').fill('2000-01-11T12:34');
	await datetimeRow.getByRole('button', { name: 'Add' }).click();

	// submit and navigate to item view
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('success');
	await page.getByRole('link', { name: 'view item' }).click();

	// confirm original data values
	const checkModelData = async () => {
		await expect(page.getByRole('row', { name: 'x_list_bool' })).toContainText('true, false');
		await expect(page.getByRole('row', { name: 'x_list_bool' })).not.toContainText('true, false,');
		await expect(page.getByRole('row', { name: 'x_list_bool' })).not.toContainText(', true, false');

		await expect(page.getByRole('row', { name: 'x_list_int' })).toContainText('7, 11');
		await expect(page.getByRole('row', { name: 'x_list_int' })).not.toContainText('7, 11,');
		await expect(page.getByRole('row', { name: 'x_list_int' })).not.toContainText(', 7, 11');

		await expect(page.getByRole('row', { name: 'x_list_float' })).toContainText('3.14, 2.718');
		await expect(page.getByRole('row', { name: 'x_list_float' })).not.toContainText('3.14, 2.718,');
		await expect(page.getByRole('row', { name: 'x_list_float' })).not.toContainText(', 3.14, 2.718');

		await expect(page.getByRole('row', { name: 'x_list_string' })).toContainText('banana');
		await expect(page.getByRole('row', { name: 'x_list_string' })).not.toContainText('banana,');
		await expect(page.getByRole('row', { name: 'x_list_string' })).not.toContainText(', banana');

		await expect(page.getByRole('row', { name: 'x_list_enum' })).toContainText('chorizo, al pastor');
		await expect(page.getByRole('row', { name: 'x_list_enum' })).not.toContainText('chorizo, al pastor,');
		await expect(page.getByRole('row', { name: 'x_list_enum' })).not.toContainText(', chorizo, al pastor');

		await expect(page.getByRole('row', { name: 'x_list_datetime' })).toContainText('2000-01-11T12:34');
		await expect(page.getByRole('row', { name: 'x_list_datetime' })).not.toContainText('2000-01-11T12:34,');
		await expect(page.getByRole('row', { name: 'x_list_datetime' })).not.toContainText(', 2000-01-11T12:34');
	};

	await checkModelData();

	//
	// test model edit form
	//

	// edit x_list_bool
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await boolRow.locator('input.list-input[type="checkbox"]').uncheck();
	await boolRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await boolRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await boolRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_int
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await intRow.locator('input.list-input').fill('99');
	await intRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await intRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await intRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_float
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await floatRow.locator('input.list-input').fill('9.99');
	await floatRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await floatRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await floatRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_string
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await stringRow.locator('input.list-input').fill('mango');
	await stringRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await stringRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await stringRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_enum
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await enumRow.locator('select.list-input').selectOption('carne');
	await enumRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await enumRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await enumRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_datetime
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await datetimeRow.locator('input.list-input[type="datetime-local"]').fill('2001-06-15T10:30');
	await datetimeRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await datetimeRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await datetimeRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// reload data and confirm values are correct
	await page.getByRole('button', { name: 'load' }).click();
	await checkModelData();
});