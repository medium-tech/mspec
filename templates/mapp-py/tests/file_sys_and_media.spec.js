import { test } from './fixtures.js';
import { expect } from '@playwright/test';

test('test file system and media flow', async ({ browser, crudEnv, crudSession }) => {

	/*
	This test covers the following:
	- Create a file record in file system module
		- test uploading a file
		- test downloading the file
	- Create a press kit record in media
		- test uploading file (sample pdf)
		- test uploading media.image (sample jpg)
		- test foreign key selection widget for file record created in previous step
	- View created press kit
		- download the brochure file
		- download the logo image file
		- navigate to the file system record via the foreign key link
	*/


	const context = await browser.newContext({ storageState: crudSession.storageState });
	const page = await context.newPage();
	
	// Navigate to index page
	await page.goto(crudEnv.host);

	//
	// create file record (for use use as foreign key in press kit)
	//

	await page.getByRole('link', { name: 'file-system' }).click();
	await page.getByRole('link', { name: 'record' }).click();
	await page.getByRole('button', { name: 'Choose File' }).click();
	await page.getByRole('button', { name: 'Choose File' }).setInputFiles('./tests/samples/lorem-document.pdf');

	await page.getByRole('row', { name: 'description:' }).getByRole('textbox').click();
	await page.getByRole('row', { name: 'description:' }).getByRole('textbox').fill('a sample pdf');
	await page.getByRole('row', { name: 'source:' }).getByRole('textbox').click();
	await page.getByRole('row', { name: 'source:' }).getByRole('textbox').fill('some website');
	await page.getByRole('row', { name: 'url:' }).getByRole('textbox').click();
	await page.getByRole('row', { name: 'note:' }).getByRole('textbox').click();
	await page.getByRole('row', { name: 'note:' }).getByRole('textbox').fill('for unittest');

	await page.getByRole('button', { name: 'Submit' }).click();
	await page.getByRole('link', { name: 'view item' }).click();

	// navigate to created record //

	await expect(page.locator('tbody')).toContainText('for unittest');
	const downloadPromise = page.waitForEvent('download');
	await page.getByRole('button', { name: 'download file' }).click();
	const download = await downloadPromise;

	//
	// create press kit
	//

	await page.getByRole('link', { name: 'dev app' }).click();
	await page.getByRole('link', { name: 'media' }).click();
	await page.getByRole('link', { name: 'press-kit' }).click();

	await page.getByRole('row', { name: 'description:' }).getByRole('textbox').click();
	await page.getByRole('row', { name: 'description:' }).getByRole('textbox').fill('Press kit for JS Unittest');
	await page.getByRole('row', { name: 'logo image: Choose File' }).getByRole('button').click();
	await page.getByRole('row', { name: 'logo image: Choose File' }).getByRole('button').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');

	await page.getByRole('row', { name: 'brochure file: Choose File' }).getByRole('button').click();
	await page.getByRole('button', { name: 'Choose File' }).setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');

	await page.getByRole('button', { name: 'Find record' }).click();
	await expect(page.locator('#lingo-app')).toContainText('for unittest');
	await page.getByRole('cell', { name: 'for unittest', exact: true }).first().click();
	await page.getByRole('button', { name: 'Submit' }).click();

	await expect(page.locator('#lingo-app')).toContainText('Success,');

	// view press kit and download files //

	await page.getByRole('link', { name: 'view item' }).click();
	await expect(page.locator('tbody')).toContainText('Press kit for JS Unittest');
	const download1Promise = page.waitForEvent('download');
	await page.getByRole('button', { name: '⬇' }).click();
	const download1 = await download1Promise;
	const download2Promise = page.waitForEvent('download');

	await page.getByRole('button', { name: 'download file' }).click();
	const download2 = await download2Promise;
	await page.getByRole('link', { name: 'go to file-system/record/' }).click();

	await expect(page.locator('tbody')).toContainText('a sample pdf');
	await expect(page.locator('tbody')).toContainText('some website');
	await expect(page.locator('tbody')).toContainText('for unittest');
});