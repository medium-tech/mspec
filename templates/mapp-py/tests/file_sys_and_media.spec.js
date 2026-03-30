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
	await page.getByRole('row', { name: 'logo image: Choose File' }).getByRole('button').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');

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

test('test foreign key list fields - file upload types', async ({ browser, crudEnv, crudSession }) => {

	/*
	This test covers the following:
	- Create a post in sosh-net module with FK list fields
		- test uploading a file to the attachments list (file_system.file FK list)
		- test uploading an image to the web images list (media.master_image FK list)
		- test uploading an image to the raw images list (media.image FK list)
		- verify each upload adds an item to the respective list
	- Edit the post and remove items from FK lists
	*/

	const context = await browser.newContext({ storageState: crudSession.storageState });
	const page = await context.newPage();

	// Navigate to sosh-net module, post model
	await page.goto(crudEnv.host);
	await page.getByRole('link', { name: 'sosh-net' }).click();
	await page.getByRole('link', { name: 'post' }).click();

	// Fill required message field
	await page.getByRole('row', { name: 'message:' }).getByRole('textbox').fill('FK list test post');

	// Add attachment (file_system.file FK list) - upload a file
	await page.getByRole('row', { name: 'attachments:' }).locator('input[type="file"]').setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');

	// Verify the attachment ID was added to the list display
	const attachmentsRow = page.getByRole('row', { name: 'attachments:' });
	await expect(attachmentsRow.locator('button.remove-button')).toHaveCount(1);

	// Upload a second attachment
	await page.getByRole('row', { name: 'attachments:' }).locator('input[type="file"]').setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');
	await expect(attachmentsRow.locator('button.remove-button')).toHaveCount(2);

	// Add web image (media.master_image FK list) - upload an image
	await page.getByRole('row', { name: 'web images:' }).locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');

	const webImagesRow = page.getByRole('row', { name: 'web images:' });
	await expect(webImagesRow.locator('button.remove-button')).toHaveCount(1);

	// Add raw image (media.image FK list) - upload an image
	await page.getByRole('row', { name: 'raw images:' }).locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');

	const rawImagesRow = page.getByRole('row', { name: 'raw images:' });
	await expect(rawImagesRow.locator('button.remove-button')).toHaveCount(1);

	// Submit the post
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success');

	// View created post and verify
	await page.getByRole('link', { name: 'view item' }).click();
	await expect(page.locator('#lingo-app')).toContainText('id');

	// Edit the post to test removing FK list items
	await page.getByRole('button', { name: 'edit' }).click();

	// Remove one attachment from the list
	const editAttachmentsRow = page.getByRole('row', { name: 'attachments:' });
	await expect(editAttachmentsRow.locator('button.remove-button')).toHaveCount(2);
	await editAttachmentsRow.locator('button.remove-button').first().click();
	await expect(editAttachmentsRow.locator('button.remove-button')).toHaveCount(1);

	// Submit updated post
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success');
});

test('test foreign key list fields - popup selection', async ({ browser, crudEnv, crudSession }) => {

	/*
	This test covers the following:
	- Create a post to use as a related post reference
	- Create a second post with related_posts FK list field
		- use popup to find and select the first post
		- verify item is added to the list
		- use popup again to add another item
	- Edit the post and remove an item from the related_posts list
	*/

	const context = await browser.newContext({ storageState: crudSession.storageState });
	const page = await context.newPage();

	// Navigate to sosh-net module, post model
	await page.goto(crudEnv.host);
	await page.getByRole('link', { name: 'sosh-net' }).click();
	await page.getByRole('link', { name: 'post' }).click();

	// Create first post to reference
	await page.getByRole('row', { name: 'message:' }).getByRole('textbox').fill('Post to reference in FK list');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success');

	// Navigate back to create a second post with related_posts
	await page.getByRole('link', { name: 'sosh-net' }).click();
	await page.getByRole('link', { name: 'post' }).click();

	await page.getByRole('row', { name: 'message:' }).getByRole('textbox').fill('Post with related posts FK list');

	// Use popup to find and select the first post for related_posts list
	await page.getByRole('row', { name: 'related posts:' }).getByRole('button', { name: 'Find post' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Post to reference in FK list');
	await page.getByRole('cell', { name: 'Post to reference in FK list', exact: true }).first().click();

	// Verify item was added to related posts list
	const relatedPostsRow = page.getByRole('row', { name: 'related posts:' });
	await expect(relatedPostsRow.locator('button.remove-button')).toHaveCount(1);

	// Use popup again to add the same post a second time
	await page.getByRole('row', { name: 'related posts:' }).getByRole('button', { name: 'Find post' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Post to reference in FK list');
	await page.getByRole('cell', { name: 'Post to reference in FK list', exact: true }).first().click();
	await expect(relatedPostsRow.locator('button.remove-button')).toHaveCount(2);

	// Submit the post
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success');

	// View and verify
	await page.getByRole('link', { name: 'view item' }).click();
	await expect(page.locator('#lingo-app')).toContainText('id');

	// Edit the post and remove one related post
	await page.getByRole('button', { name: 'edit' }).click();

	const editRelatedPostsRow = page.getByRole('row', { name: 'related posts:' });
	await expect(editRelatedPostsRow.locator('button.remove-button')).toHaveCount(2);
	await editRelatedPostsRow.locator('button.remove-button').first().click();
	await expect(editRelatedPostsRow.locator('button.remove-button')).toHaveCount(1);

	// Submit updated post
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success');
});