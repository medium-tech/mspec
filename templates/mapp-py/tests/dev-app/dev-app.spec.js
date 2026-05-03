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

test('edit form state - single-choice-fk', async ({ browser, crudEnv }) => {

	/*
		Check edit form state for single choice foreign key fields
			- ensure that selecting a FK via popup triggers the (modified indicator)
			- ensure that uploading a file for file FK fields triggers the (modified indicator)
			- ensure that canceling reverts the form to the original values
	*/

	// create user and login
	const userSession = await createAndLoginUser(crudEnv.host, browser, 'single-fk');
	const context = await browser.newContext({ storageState: userSession.storageState });
	const page = await context.newPage();
	await context.addCookies([{ name: 'protocol_mode', value: 'true', domain: new URL(crudEnv.host).hostname, path: '/' }]);

	//
	// pre-seed 2 single_choice_fields records for FK popup selection
	//

	for (let i = 0; i < 2; i++) {
		await page.goto(crudEnv.host);
		await page.getByRole('link', { name: 'model-type-tests' }).click();
		await page.getByRole('link', { name: 'single-choice-fields' }).click();
		await page.getByRole('row', { name: 'x bool:' }).getByRole('checkbox').uncheck();
		await page.getByRole('row', { name: 'x int:' }).getByRole('spinbutton').fill(String(i + 1));
		await page.getByRole('row', { name: 'x float:' }).getByRole('textbox').fill(`${i + 1}.0`);
		await page.getByRole('row', { name: 'x string:' }).getByRole('textbox').fill(`seed-${i}`);
		await page.getByRole('row', { name: 'x enum:' }).getByRole('combobox').selectOption('taco');
		await page.getByRole('row', { name: 'x datetime:' }).getByRole('textbox').fill('2000-01-01T00:00');
		await page.getByRole('button', { name: 'Submit' }).click();
		await expect(page.locator('#lingo-app')).toContainText('success');
	}

	//
	// create single-choice-fk model
	//

	await page.goto(crudEnv.host);
	await page.getByRole('link', { name: 'model-type-tests' }).click();
	await page.getByRole('link', { name: 'single-choice-fk' }).click();

	const xFkFieldRow = page.getByRole('row', { name: 'x fk field:' });
	const xFkFileRow = page.getByRole('row', { name: 'x fk file:' });
	const xFkImageRow = page.getByRole('row', { name: 'x fk image:' });
	const xFkMasterImageRow = page.getByRole('row', { name: 'x fk master image:' });

	// x_fk_field: select 1st pre-seeded record via popup
	await xFkFieldRow.getByRole('button', { name: 'Find single_choice_fields' }).click();
	await expect(page.locator('#lingo-app')).not.toContainText('pending');
	await page.locator('.popup-content > div > table > tbody > tr').first().click();
	await expect(xFkFieldRow.getByRole('textbox')).not.toHaveValue('-1');
	const xFkFieldValue = await xFkFieldRow.getByRole('textbox').inputValue();
	const xFkFieldValueLinkText = `go to model-type-tests/single-choice-fields/${xFkFieldValue}`;

	// x_fk_file: upload a PDF file
	await xFkFileRow.locator('input[type="file"]').setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');
	await expect(xFkFileRow.getByRole('button', { name: 'Reset' })).toBeVisible();
	await expect(xFkFileRow.getByRole('textbox')).not.toHaveValue('-1');
	const xFkFileValue = await xFkFileRow.getByRole('textbox').inputValue();

	// x_fk_image: upload an image file
	await xFkImageRow.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');
	await expect(xFkImageRow.getByRole('textbox')).not.toHaveValue('-1');
	const xFkImageValue = await xFkImageRow.getByRole('textbox').inputValue();

	// x_fk_master_image: upload a master image file
	await xFkMasterImageRow.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');
	await expect(xFkMasterImageRow.getByRole('textbox')).not.toHaveValue('-1');
	const xFkMasterImageValue = await xFkMasterImageRow.getByRole('textbox').inputValue();

	// submit and navigate to item view
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('success');
	await page.getByRole('link', { name: 'view item' }).click();

	// confirm original data values
	const checkModelData = async () => {
		await expect(page.getByRole('row', { name: 'x_fk_field' }).getByRole('link', { name: xFkFieldValueLinkText })).toBeVisible();

		await expect(page.getByRole('row', { name: 'x_fk_file' }).getByRole('button', { name: 'download file' })).toBeVisible();
		await expect(page.getByRole('row', { name: 'x_fk_file' })).toContainText(xFkFileValue);

		await expect(page.getByRole('row', { name: 'x_fk_image' }).locator('.viewer-container')).toBeVisible();
		await expect(page.getByRole('row', { name: 'x_fk_image' })).toContainText(xFkImageValue);

		await expect(page.getByRole('row', { name: 'x_fk_master_image' }).locator('.viewer-container')).toBeVisible();
		await expect(page.getByRole('row', { name: 'x_fk_master_image' })).toContainText(xFkMasterImageValue);
	};

	await checkModelData();

	//
	// test model edit form
	//

	// edit x_fk_field: select a different record (index 1) to trigger (modified)
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await xFkFieldRow.getByRole('button', { name: 'Find single_choice_fields' }).click();
	await expect(page.locator('#lingo-app')).not.toContainText('pending');
	await page.locator('.popup-content > div > table > tbody > tr').nth(1).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_fk_file: upload a new file to trigger (modified)
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await xFkFileRow.locator('input[type="file"]').setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_fk_image: upload a new image to trigger (modified)
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await xFkImageRow.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_fk_master_image: upload a new image to trigger (modified)
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await xFkMasterImageRow.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// reload data and confirm values are correct
	await page.getByRole('button', { name: 'load', exact: true }).click();
	await checkModelData();
});

test('edit form state - multi-choice-fk', async ({ browser, crudEnv }) => {

	/*
		Check edit form state for multi choice (list) foreign key fields
			- ensure that adding a FK item via popup triggers the (modified indicator)
			- ensure that uploading a file for file FK list fields triggers the (modified indicator)
			- ensure that the remove button count is correct after adding an item
			- ensure that canceling reverts the list to the original values
	*/

	// create user and login
	const userSession = await createAndLoginUser(crudEnv.host, browser, 'multi-fk');
	const context = await browser.newContext({ storageState: userSession.storageState });
	const page = await context.newPage();
	await context.addCookies([{ name: 'protocol_mode', value: 'true', domain: new URL(crudEnv.host).hostname, path: '/' }]);

	//
	// pre-seed 2 single_choice_fields records for FK popup selection
	//

	for (let i = 0; i < 2; i++) {
		await page.goto(crudEnv.host);
		await page.getByRole('link', { name: 'model-type-tests' }).click();
		await page.getByRole('link', { name: 'single-choice-fields' }).click();
		await page.getByRole('row', { name: 'x bool:' }).getByRole('checkbox').uncheck();
		await page.getByRole('row', { name: 'x int:' }).getByRole('spinbutton').fill(String(i + 1));
		await page.getByRole('row', { name: 'x float:' }).getByRole('textbox').fill(`${i + 1}.0`);
		await page.getByRole('row', { name: 'x string:' }).getByRole('textbox').fill(`seed-${i}`);
		await page.getByRole('row', { name: 'x enum:' }).getByRole('combobox').selectOption('taco');
		await page.getByRole('row', { name: 'x datetime:' }).getByRole('textbox').fill('2000-01-01T00:00');
		await page.getByRole('button', { name: 'Submit' }).click();
		await expect(page.locator('#lingo-app')).toContainText('success');
	}

	//
	// create multi-choice-fk model with 1 item per FK list
	//

	await page.goto(crudEnv.host);
	await page.getByRole('link', { name: 'model-type-tests' }).click();
	await page.getByRole('link', { name: 'multi-choice-fk' }).click();

	const xListFkFieldRow = page.getByRole('row', { name: 'x list fk field:' });
	const xListFkFileRow = page.getByRole('row', { name: 'x list fk file:' });
	const xListFkImageRow = page.getByRole('row', { name: 'x list fk image:' });
	const xListFkMasterImageRow = page.getByRole('row', { name: 'x list fk master image:' });

	// x_list_fk_field: select 1st pre-seeded record (1 item)
	await xListFkFieldRow.getByRole('button', { name: 'Find single_choice_fields' }).click();
	await expect(page.locator('#lingo-app')).not.toContainText('pending');
	await page.locator('.popup-content > div > table > tbody > tr').first().click();
	await expect(xListFkFieldRow.locator('button.remove-button')).toHaveCount(1);

	// x_list_fk_file: upload 1 PDF file
	await xListFkFileRow.locator('input[type="file"]').setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(xListFkFileRow.locator('button.remove-button')).toHaveCount(1);

	// x_list_fk_image: upload 1 image
	await xListFkImageRow.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(xListFkImageRow.locator('button.remove-button')).toHaveCount(1);

	// x_list_fk_master_image: upload 1 image
	await xListFkMasterImageRow.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(xListFkMasterImageRow.locator('button.remove-button')).toHaveCount(1);

	// submit and navigate to item view
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('success');
	await page.getByRole('link', { name: 'view item' }).click();

	// confirm original data values (1 item per FK list field)
	const checkModelData = async () => {
		await expect(page.getByRole('row', { name: 'x_list_fk_field' }).getByRole('link', { name: /go to/ })).toHaveCount(1);
		await expect(page.getByRole('row', { name: 'x_list_fk_file' }).getByRole('button', { name: /^⬇/ })).toHaveCount(1);
		await expect(page.getByRole('row', { name: 'x_list_fk_image' }).locator('.viewer-container')).toBeVisible();
		await expect(page.getByRole('row', { name: 'x_list_fk_master_image' }).locator('.viewer-container')).toBeVisible();
	};

	await checkModelData();

	//
	// test model edit form
	//

	// edit x_list_fk_field: add a 2nd FK item (index 1) to trigger (modified)
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(xListFkFieldRow.locator('button.remove-button')).toHaveCount(1);
	await xListFkFieldRow.getByRole('button', { name: 'Find single_choice_fields' }).click();
	await expect(page.locator('#lingo-app')).not.toContainText('pending');
	await page.locator('.popup-content > div > table > tbody > tr').nth(1).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(xListFkFieldRow.locator('button.remove-button')).toHaveCount(2);
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_fk_file: upload a 2nd file to trigger (modified)
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(xListFkFileRow.locator('button.remove-button')).toHaveCount(1);
	await xListFkFileRow.locator('input[type="file"]').setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(xListFkFileRow.locator('button.remove-button')).toHaveCount(2);
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_fk_image: upload a 2nd image to trigger (modified)
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(xListFkImageRow.locator('button.remove-button')).toHaveCount(1);
	await xListFkImageRow.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(xListFkImageRow.locator('button.remove-button')).toHaveCount(2);
	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_fk_master_image: upload a 2nd image to trigger (modified)
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(xListFkMasterImageRow.locator('button.remove-button')).toHaveCount(1);
	await xListFkMasterImageRow.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(xListFkMasterImageRow.locator('button.remove-button')).toHaveCount(2);
	await page.getByRole('button', { name: 'cancel' }).click();
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

	// check that bool row has 1 add button and 2 remove buttons (for the 2 existing items)
	await expect(boolRow.getByRole('button', { name: 'Add' })).toHaveCount(1);
	await expect(boolRow.locator('button.remove-button')).toHaveCount(2);

	await boolRow.locator('input.list-input[type="checkbox"]').uncheck();
	await boolRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(boolRow.locator('button.remove-button')).toHaveCount(3);

	await boolRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(boolRow.locator('button.remove-button')).toHaveCount(2);

	await boolRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(boolRow.locator('button.remove-button')).toHaveCount(1);

	await boolRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(boolRow.locator('button.remove-button')).toHaveCount(0);

	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_int
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');

	// check that int row has 1 add button and 2 remove buttons (for the 2 existing items)
	await expect(intRow.getByRole('button', { name: 'Add' })).toHaveCount(1);
	await expect(intRow.locator('button.remove-button')).toHaveCount(2);

	await intRow.locator('input.list-input').fill('99');
	await intRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(intRow.locator('button.remove-button')).toHaveCount(3);

	await intRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(intRow.locator('button.remove-button')).toHaveCount(2);

	await intRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(intRow.locator('button.remove-button')).toHaveCount(1);

	await intRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(intRow.locator('button.remove-button')).toHaveCount(0);

	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_float
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');

	// check that float row has 1 add button and 2 remove buttons (for the 2 existing items)
	await expect(floatRow.getByRole('button', { name: 'Add' })).toHaveCount(1);
	await expect(floatRow.locator('button.remove-button')).toHaveCount(2);

	await floatRow.locator('input.list-input').fill('9.99');
	await floatRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(floatRow.locator('button.remove-button')).toHaveCount(3);

	await floatRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(floatRow.locator('button.remove-button')).toHaveCount(2);

	await floatRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(floatRow.locator('button.remove-button')).toHaveCount(1);
	
	await floatRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(floatRow.locator('button.remove-button')).toHaveCount(0);

	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_string
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');

	// check that string row has 1 add button and 1 remove button (for the 1 existing item)
	await expect(stringRow.getByRole('button', { name: 'Add' })).toHaveCount(1);
	await expect(stringRow.locator('button.remove-button')).toHaveCount(1);

	await stringRow.locator('input.list-input').fill('mango');
	await stringRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(stringRow.locator('button.remove-button')).toHaveCount(2);

	await stringRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(stringRow.locator('button.remove-button')).toHaveCount(1);

	await stringRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(stringRow.locator('button.remove-button')).toHaveCount(0);

	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_enum
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');

	// check that enum row has 1 add button and 2 remove buttons (for the 2 existing items)
	await expect(enumRow.getByRole('button', { name: 'Add' })).toHaveCount(1);
	await expect(enumRow.locator('button.remove-button')).toHaveCount(2);

	await enumRow.locator('select.list-input').selectOption('carne');
	await enumRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(enumRow.locator('button.remove-button')).toHaveCount(3);

	await enumRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(enumRow.locator('button.remove-button')).toHaveCount(2);

	await enumRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(enumRow.locator('button.remove-button')).toHaveCount(1);
	
	await enumRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(enumRow.locator('button.remove-button')).toHaveCount(0);

	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// edit x_list_datetime
	await page.getByRole('button', { name: 'edit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('editing');
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');

	// check that datetime row has 1 add button and 1 remove button (for the 1 existing item)
	await expect(datetimeRow.getByRole('button', { name: 'Add' })).toHaveCount(1);
	await expect(datetimeRow.locator('button.remove-button')).toHaveCount(1);

	await datetimeRow.locator('input.list-input[type="datetime-local"]').fill('2001-06-15T10:30');
	await datetimeRow.getByRole('button', { name: 'Add' }).click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(datetimeRow.locator('button.remove-button')).toHaveCount(2);

	await datetimeRow.locator('button.remove-button').last().click();
	await expect(page.locator('#lingo-app')).not.toContainText('(modified)');
	await expect(datetimeRow.locator('button.remove-button')).toHaveCount(1);

	await datetimeRow.locator('button.remove-button').first().click();
	await expect(page.locator('#lingo-app')).toContainText('(modified)');
	await expect(datetimeRow.locator('button.remove-button')).toHaveCount(0);

	await page.getByRole('button', { name: 'cancel' }).click();
	await checkModelData();

	// reload data and confirm values are correct
	await page.getByRole('button', { name: 'load' }).click();
	await checkModelData();
});