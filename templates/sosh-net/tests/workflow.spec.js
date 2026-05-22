import { test } from './fixtures.js';
import { expect } from '@playwright/test';

//
// helper functions
//

async function createAccount(page, host, uniqueId) {
	const email = `workflow-${uniqueId}@example.com`;
	const password = `pw${uniqueId}`;

	await page.goto(host);
	await page.getByRole('link', { name: 'enter social' }).click();
	await page.getByRole('link', { name: 'account' }).click();
	await page.waitForSelector('#lingo-app');

	// create account form appears after the login form on this page
	// 'name: Name of the user' row is unique to the create account form
	await page.getByRole('row', { name: 'name: Name of the user' }).getByRole('textbox').fill(`Workflow User ${uniqueId}`);
	// second 'email:' row belongs to the create account form
	await page.getByRole('row', { name: 'email: Email of the user' }).nth(1).getByRole('textbox').fill(email);
	// second 'password:' row belongs to the create account form
	await page.getByRole('row', { name: 'password: show' }).nth(1).getByRole('textbox').fill(password);
	// 'password confirm:' row is unique to the create account form
	await page.getByRole('row', { name: 'password confirm: show' }).getByRole('textbox').fill(password);
	await page.getByRole('button', { name: 'create account' }).click();
	await expect(page.locator('#lingo-app')).toContainText('success', { timeout: 10000 });

	return { email, password };
}

async function loginUser(page, host, email, password) {
	await page.goto(host);
	await page.getByRole('link', { name: 'enter social' }).click();
	await page.getByRole('link', { name: 'account' }).click();
	await page.waitForSelector('#lingo-app');

	// login form is first on the page (before the create account form)
	await page.getByRole('row', { name: 'email: Email of the user' }).first().getByRole('textbox').fill(email);
	await page.getByRole('row', { name: 'password: show' }).first().getByRole('textbox').fill(password);
	await page.getByRole('button', { name: 'login' }).click();

	await expect(page.getByRole('heading', { name: ':: login' })).not.toBeVisible({ timeout: 10000 });
	await expect(page.getByRole('button', { name: 'logout' })).toBeVisible({ timeout: 10000 });
}

async function createProfile(page, host, uniqueId) {
	await page.goto(host);
	await page.getByRole('link', { name: 'enter social' }).click();
	await page.getByRole('link', { name: 'profiles' }).click();
	await page.getByRole('link', { name: 'your profile' }).click();
	await expect(page.getByRole('heading', { name: ':: create profile' })).toBeVisible({ timeout: 10000 });

	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(`user_${uniqueId}`);
	const editor = page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor');
	await editor.fill(`Bio for workflow user ${uniqueId}`);

	const profile_pic_row = page.getByRole('row', { name: 'profile picture:' });
	await profile_pic_row.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');
	await expect(page.locator('#lingo-app')).not.toContainText('error');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success', { timeout: 10000 });
}

async function createForumAndThread(page, host, uniqueId) {
	await page.goto(host);
	await page.getByRole('link', { name: 'enter social' }).click();
	await page.getByRole('link', { name: 'forums' }).click();
	await page.waitForSelector('#lingo-app');

	// create a forum
	await page.getByRole('button', { name: 'create forum' }).click();
	await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(`Workflow Forum ${uniqueId}`);
	const editor = await page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor');
	await editor.fill(`Forum for workflow test ${uniqueId}`);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success', { timeout: 10000 });

	// navigate to the created forum via the 'view item' link
	await page.getByRole('link', { name: 'view item' }).click();
	await page.waitForSelector('#lingo-app');

	// extract forum id from url
	const forumUrl = page.url();
	// expects /social/forum/{id}
	const forumIdMatch = forumUrl.match(/\/forum\/(\d+)/);
	const forumId = forumIdMatch ? forumIdMatch[1] : null;

	// create a thread in the forum
	await page.getByRole('button', { name: 'create thread' }).click();
	await page.getByRole('row', { name: 'title:' }).getByRole('textbox').fill(`Workflow Thread ${uniqueId}`);
	await page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor').fill(`Thread message for workflow test ${uniqueId}`);
	await page.getByRole('button', { name: 'Submit' }).click();
	// create-thread op shows 'view thread' link on success (not the generic 'success' text)
	await expect(page.getByRole('link', { name: 'view thread' })).toBeVisible({ timeout: 10000 });

	// click 'view thread' to go to thread instance
	await page.getByRole('link', { name: 'view thread' }).click();
	await page.waitForSelector('#lingo-app');

	// extract thread id from url
	const threadUrl = page.url();
	// expects /social/thread/{id}
	const threadIdMatch = threadUrl.match(/\/thread\/(\d+)/);
	const threadId = threadIdMatch ? threadIdMatch[1] : null;

	return { forumId, threadId };
}

async function logoutUser(page, host) {
	await page.goto(host);
	await page.getByRole('link', { name: 'enter social' }).click();
	await page.getByRole('link', { name: 'account' }).click();
	await page.waitForSelector('#lingo-app');
	await page.getByRole('button', { name: 'logout' }).click();
	// after logout the login section becomes visible again
	await expect(page.getByRole('heading', { name: ':: login' })).toBeVisible({ timeout: 10000 });
}

async function leaveReply(page, message) {
	// ':: add reply' section is at the bottom of the thread instance page
	await expect(page.locator('#lingo-app')).not.toContainText('🟡', { timeout: 10000 });
	await expect(page.getByRole('heading', { name: ':: add reply' })).toBeVisible({ timeout: 10000 });


	await page.locator('div.rich-text-editor').fill(message);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('success', { timeout: 10000 });
}

//
// workflow test
//

test('test user workflow', async ({ browser, crudEnv }) => {
	const host = crudEnv.host;

	//
	// front page
	//

	const initialContext = await browser.newContext();
	const initialPage = await initialContext.newPage();
	await initialPage.goto(host);

	// confirm front page has custom content
	await expect(initialPage.getByRole('heading')).toContainText('medium tech');
	await expect(initialPage.locator('span')).toContainText('-->');
	// confirm front page does not have protocol_mode content
	await expect(initialPage.locator('#lingo-app')).not.toContainText(':: social');
	await expect(initialPage.locator('#lingo-app')).not.toContainText(':: available modules');

	//
	// social main page
	//

	await initialPage.getByRole('link', { name: 'enter social' }).click();
	await expect(initialPage.locator('h1')).toContainText('social');
	await expect(initialPage.getByRole('link', { name: 'mtech' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'social' })).toBeVisible();
	await expect(initialPage.locator('h2')).toContainText(':: the network');
	await expect(initialPage.getByRole('link', { name: 'profiles' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'forums' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'account' })).toBeVisible();
	await expect(initialPage.locator('#lingo-app')).toContainText('this is social.');
	// await initialContext.close();

	//
	// phase 1: create 2 users with profiles, forums, and threads
	//

	const users = [];

	for (let i = 0; i < 2; i++) {
		// multiply by 1000 and add i to guarantee uniqueness even within the same millisecond
		const uniqueId = Date.now() * 1000 + i;
		const userContext = await browser.newContext();
		const page = await userContext.newPage();

		const { email, password } = await createAccount(page, host, uniqueId);
		await loginUser(page, host, email, password);
		await createProfile(page, host, uniqueId);
		await createForumAndThread(page, host, uniqueId);
		await logoutUser(page, host);

		await userContext.close();
		users.push({ email, password });
	}

	//
	// phase 2: each user logs in, interacts, logs out, then checks auth errors
	//

	let userIndex = 0;

	for (const user of users) {
		const userContext = await browser.newContext();
		const page = await userContext.newPage();

		// login
		await loginUser(page, host, user.email, user.password);

		// navigate to profiles page and click on the first profile
		await page.goto(`${host}/social/profile`);
		await page.waitForSelector('tr.list-selecting', { timeout: 10000 });
		await page.locator('tr.list-selecting').first().click();
		await page.waitForSelector('#lingo-app');

		// navigate to forums and click on the first forum
		await page.goto(`${host}/social/forum`);
		await page.locator('tr').filter({ hasText: 'Workflow Forum' }).first().click();			// this could have race confitions w/ parallel tests
		// if the first Workflow Forum is not on page 1
		// navigate to first forum																// but we need to wait for a Workflow Forum/Thread to ensure
		await expect(page.locator('h1')).toContainText(':: forum ::', { timeout: 10000 });		// the crud test hasn't deleted the thread

		// click on the first thread in the forum
		// await page.locator('tr.list-selecting').first().click();
		await page.locator('tr').filter({ hasText: 'Workflow Thread' }).first().click();		// this could have race conditions w/ parallel tests
		// if the first Workflow Thread is not on page 1
		// but we need to wait for a Workflow Forum/Thread to ensure
		// leave a reply on the thread															// the crud test hasn't deleted the thread
		await leaveReply(page, `Reply from workflow user ${user.email}`);
		const reaction = userIndex === 0 ? '❤️' : '👍'
		await page.getByRole('combobox').first().selectOption(reaction);
		await page.getByRole('button', { name: 'react' }).first().click();
		await page.reload();
		await expect(page.locator('#lingo-app')).not.toContainText('error', { timeout: 5000, ignoreCase: true });
		await expect(page.locator('#lingo-app')).toContainText(`your reaction: ${reaction}`);

		// logout
		await logoutUser(page, host);

		// --- error checks when not logged in ---

		// profile list requires login
		await page.goto(`${host}/social/profile`);
		await expect(page.locator('#lingo-app')).toContainText('Error: Not logged in', { timeout: 10000, ignoreCase: true });

		// profile instance requires login
		await page.goto(`${host}/social/profile/1`);
		await expect(page.locator('#lingo-app')).toContainText('Error: Not logged in', { timeout: 10000, ignoreCase: true });

		// forum list requires login
		await page.goto(`${host}/social/forum`);
		await expect(page.locator('#lingo-app')).toContainText('Error: Not logged in', { timeout: 10000, ignoreCase: true });

		// forum instance op returns a server error when not logged in
		await page.goto(`${host}/social/forum/1`);
		await expect(page.locator('#lingo-app')).toContainText('Contact support or check logs for details', { timeout: 10000, ignoreCase: true });

		// thread instance op returns a server error when not logged in
		await page.goto(`${host}/social/thread/1`);
		await expect(page.locator('#lingo-app')).toContainText('Contact support or check logs for details', { timeout: 10000, ignoreCase: true });

		await userContext.close();

		userIndex++;
	}

	//
	// phase 3: confirm user must have profile to create forums/threads/replies
	//

	// this coverted in this test because we already have seeded threads and forums to work with

	// create user w/o profile
	const page = await initialContext.newPage();
	await page.goto(host);
	const uniqueId = Date.now() * 1000;
	const { email, password } = await createAccount(page, host, uniqueId);
	await loginUser(page, host, email, password);

	// cannot create forum without profile
	await page.goto(`${host}/social/forum`);
	await page.getByRole('button', { name: 'create forum' }).click();
	await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill('Can\t Create a Forum');
	await page.locator('div').nth(4).fill('Because I haven\'t made a profile!');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.getByRole('table')).toContainText('error');
	await expect(page.locator('#lingo-app')).toContainText('Model Validation failed for: Forum');
	await expect(page.getByRole('table')).toContainText('You must have a profile to create items');
	await page.getByRole('link', { name: 'forum' }).click();

	// cannot create thread without profile
	await page.locator('tr').nth(1).click();
	await page.getByRole('button', { name: 'create thread' }).click();
	await page.getByRole('textbox').click();
	await page.getByRole('textbox').fill('Can\'t Create a Thread');
	await page.locator('.rich-text-editor').click();
	await page.locator('.rich-text-editor').fill('Because I don\'t have a profile!');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.getByRole('table')).toContainText('error');
	await expect(page.getByRole('table')).toContainText('You must have a profile to create items');

	// cannot reply to thread without profile
	await page.goto(`${host}/social/forum`);
	await page.locator('tr').nth(1).click();
	await page.locator('tr').nth(2).click();
	await page.locator('.rich-text-editor').click();
	await page.locator('.rich-text-editor').fill('I can\'t reply without a profile!');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('error');
	await expect(page.locator('#lingo-app')).toContainText('You must have a profile to create items');
});

test('test navigation links', async ({ browser, crudEnv }) => {
	const host = crudEnv.host;

	const uniqueId = Date.now() * 1000;
	const userContext = await browser.newContext();
	const page = await userContext.newPage();

	const { email, password } = await createAccount(page, host, uniqueId);
	await loginUser(page, host, email, password);
	await createProfile(page, host, uniqueId);
	const { forumId, threadId } = await createForumAndThread(page, host, uniqueId);

	//
	// main pages
	//

	// index page - links to social
	await page.goto(host);
	await expect(page.getByRole('heading')).toContainText('medium tech');
	await page.getByRole('link', { name: 'enter social' }).click();

	// social main page - breadcrumbs and links back to main
	await expect(page.locator('h1')).toContainText('social');
	await expect(page.locator('h2')).toContainText(':: the network');
	await expect(page.locator('#lingo-app')).toContainText('this is social.');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h1')).toContainText('social');
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText('medium tech');
	await page.getByRole('link', { name: 'enter social' }).click();
	await expect(page.locator('h1')).toContainText('social');

	// profiles
	await page.getByRole('link', { name: 'profiles' }).click();
	await expect(page.locator('h2')).toContainText(':: profiles');

	// your profile - breadcrumbs to main
	await page.getByRole('link', { name: 'your profile' }).click();
	await expect(page.locator('h2')).toContainText(':: your profile');
	await page.getByRole('link', { name: 'yours' }).click();
	await expect(page.locator('h2')).toContainText(':: your profile');
	await page.getByRole('link', { name: 'profile', exact: true }).click();
	await expect(page.locator('h2')).toContainText(':: profiles');
	await page.getByRole('link', { name: 'your profile' }).click();
	await expect(page.locator('h2')).toContainText(':: your profile');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h2')).toContainText(':: the network');
	await page.getByRole('link', { name: 'profiles' }).click();
	await page.getByRole('link', { name: 'your profile' }).click();
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText('medium tech');
	await page.getByRole('link', { name: 'enter social' }).click();
	await page.getByRole('link', { name: 'profiles' }).click();

	// profile main page - breadcrumbs
	await page.getByRole('link', { name: 'profile', exact: true }).click();
	await expect(page.locator('h2')).toContainText(':: profiles');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h2')).toContainText(':: the network');
	await page.getByRole('link', { name: 'profiles' }).click();
	await expect(page.locator('h2')).toContainText(':: profiles');
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText('medium tech');
	await page.getByRole('link', { name: 'enter social' }).click();

	// forum list breadcrumbs
	await page.getByRole('link', { name: 'forums' }).click();
	await page.getByRole('link', { name: 'forum' }).click();
	await expect(page.locator('h2')).toContainText(':: search forums');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h2')).toContainText(':: the network');
	await page.getByRole('link', { name: 'forums' }).click();
	await expect(page.locator('h2')).toContainText(':: search forums');
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText('medium tech');
	await page.getByRole('link', { name: 'enter social' }).click();

	// view forum breadcrumbs (use forumId for direct navigation)
	await page.goto(`${host}/social/forum/${forumId}`);
	await expect(page.locator('h1')).toContainText(':: forum ::');
	await page.getByRole('link').nth(3).click();
	await expect(page.locator('h1')).toContainText(':: forum ::');
	await page.getByRole('link', { name: 'forum' }).click();
	await expect(page.locator('h2')).toContainText(':: search forums');

	await page.goto(`${host}/social/forum/${forumId}`);
	await expect(page.locator('h1')).toContainText(':: forum ::');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h2')).toContainText(':: the network');
	await page.goto(`${host}/social/forum/${forumId}`);
	await expect(page.locator('h1')).toContainText(':: forum ::');
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText('medium tech');

	// view thread breadcrumbs (use threadId for direct navigation)
	await page.goto(`${host}/social/thread/${threadId}`);
	await expect(page.locator('h1')).toContainText(':: thread ::');
	await page.getByRole('link').nth(4).click();
	await expect(page.locator('h1')).toContainText(':: forum ::');

	await page.goto(`${host}/social/thread/${threadId}`);
	await page.getByRole('link').nth(3).click();
	await expect(page.locator('h1')).toContainText(':: forum ::');

	await page.goto(`${host}/social/thread/${threadId}`);
	await expect(page.locator('h1')).toContainText(':: thread ::');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h2')).toContainText(':: the network');
	await page.goto(`${host}/social/thread/${threadId}`);
	await expect(page.locator('h1')).toContainText(':: thread ::');
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText('medium tech');

	// account page breadcrumbs
	await page.goto(`${host}/social/account`);
	await expect(page.locator('h2')).toContainText(':: account');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h2')).toContainText(':: the network');
	await page.getByRole('link', { name: 'account' }).click();
	await expect(page.locator('h2')).toContainText(':: account');
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText('medium tech');
});

test('test create user with duplicate email', async ({ browser, crudEnv }) => {

	// init //

	const uniqueId = new Date().getTime();
	const email = `dupe-sosh-${uniqueId}@email.com`;
	const testPassword = 'test-password-123';

	const host = crudEnv.host;
	const initialContext = await browser.newContext();
	const page = await initialContext.newPage();
	await page.goto(host);

	// go to form and fill out //
	await page.goto(host);
	await page.getByRole('link', { name: 'enter social' }).click();
	await page.getByRole('link', { name: 'account' }).click();
	await page.getByRole('row', { name: 'name:' }).getByRole('textbox').fill('Dupe Email Test');
	await page.getByRole('row', { name: 'email:' }).nth(1).getByRole('textbox').fill(email);
	await page.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill(testPassword);
	await page.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill(testPassword);

	// create user //
	await page.getByRole('button', { name: 'create account' }).click();
	await expect(page.locator('#lingo-app')).toContainText('success');

	// attempt to create user again with same email //
	await page.getByRole('button', { name: 'create account' }).click();
	await expect(page.getByRole('table').nth(1)).toContainText('Could not create user: email already exists');

});

test('test create user with bad passwords', async ({ browser, crudEnv }) => {

	// init //

	const uniqueId = new Date().getTime();
	const email = `bad-pw-sosh-${uniqueId}@email.com`;

	const host = crudEnv.host;
	const initialContext = await browser.newContext();
	const page = await initialContext.newPage();

	// go to form and fill out //
	await page.goto(host);
	await page.getByRole('link', { name: 'enter social' }).click();
	await page.getByRole('link', { name: 'account' }).click();

	await page.getByRole('row', { name: 'name:' }).getByRole('textbox').fill('Bad Pass Test');
	await page.getByRole('row', { name: 'email:' }).nth(1).getByRole('textbox').fill(email);

	// short password
	await page.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill('1');
	await page.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill('1');
	await page.getByRole('button', { name: 'create account' }).click();
	await expect(page.getByRole('table').nth(1)).toContainText('Could not create user password: Password must be at least');

	// mismatched password confirmation
	await page.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill('1234567890123');
	await page.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill('0234567890123');
	await page.getByRole('button', { name: 'create account' }).click();
	await expect(page.getByRole('table').nth(1)).toContainText('Could not create user password_confirm: Confirmation does not match');

});

test('test validation errors', async ({ browser, crudEnv }) => {

	//
	// init
	//

	const host = crudEnv.host;
	const initialContext = await browser.newContext();
	const initialPage = await initialContext.newPage();

	await initialPage.goto(host);
	await initialPage.goto('http://localhost:8008/');
	const uniqueId = Date.now();

	const goodEmail = `test-validation-errors-${uniqueId}@example.com`;
	const longEmail = 'a'.repeat(1001) + '@example.com';
	const longStr = 'a'.repeat(1001);
	const longRichText = 'a'.repeat(25001);

	//
	// login validation errors
	//

	// long email
	await initialPage.goto(`${host}/social/account`);
	await initialPage.getByRole('table').filter({ hasText: 'email:Email of the userpassword:showlogin' }).locator('input[type="text"]').fill(longEmail);
	await initialPage.getByRole('table').filter({ hasText: 'email:Email of the userpassword:showlogin' }).locator('input[type="password"]').fill('test-password-456');
	await initialPage.getByRole('button', { name: 'login' }).click();
	await expect(initialPage.locator('#lingo-app')).toContainText('Field "email" exceeds max length of 1000 characters.');

	// invalid password
	await initialPage.reload();
	await initialPage.getByRole('table').filter({ hasText: 'email:Email of the userpassword:showlogin' }).locator('input[type="text"]').fill(goodEmail);
	await initialPage.getByRole('table').filter({ hasText: 'email:Email of the userpassword:showlogin' }).locator('input[type="password"]').fill(longStr);
	await initialPage.getByRole('button', { name: 'login' }).click();
	await expect(initialPage.locator('#lingo-app')).toContainText('Field "password" exceeds max length of 1000 characters.');

	//
	// create account validation errors
	//

	// invalid name
	await initialPage.reload();
	await initialPage.getByRole('row', { name: 'name:' }).getByRole('textbox').fill(longStr);
	await initialPage.getByRole('row', { name: 'email:' }).nth(1).getByRole('textbox').fill(`test-validation-errors-${uniqueId}@example.com`);
	await initialPage.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill('test-password-456');
	await initialPage.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill('test-password-456');
	await initialPage.getByRole('button', { name: 'create account' }).click();
	await expect(initialPage.locator('#lingo-app')).toContainText('Field "name" exceeds max length of 1000 characters.');

	// invalid email
	await initialPage.reload();
	await initialPage.getByRole('row', { name: 'name:' }).getByRole('textbox').fill('John Doe');
	await initialPage.getByRole('row', { name: 'email:' }).nth(1).getByRole('textbox').fill(`not-an-email-address`);
	await initialPage.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill('test-password-456');
	await initialPage.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill('test-password-456');
	await initialPage.getByRole('button', { name: 'create account' }).click();
	await expect(initialPage.locator('#lingo-app')).toContainText('invalid email format', { ignoreCase: true });

	// long email
	await initialPage.reload();
	await initialPage.getByRole('row', { name: 'name:' }).getByRole('textbox').fill('John Doe');
	await initialPage.getByRole('row', { name: 'email:' }).nth(1).getByRole('textbox').fill(longEmail);
	await initialPage.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill('test-password-456');
	await initialPage.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill('test-password-456');
	await initialPage.getByRole('button', { name: 'create account' }).click();
	await expect(initialPage.locator('#lingo-app')).toContainText('Field "email" exceeds max length of 1000 characters.');

	// password mismatch
	await initialPage.reload();
	await initialPage.getByRole('row', { name: 'name:' }).getByRole('textbox').fill('John Doe');
	await initialPage.getByRole('row', { name: 'email:' }).nth(1).getByRole('textbox').fill(goodEmail);
	await initialPage.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill('test-password-456');
	await initialPage.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill('test-password-4567');
	await initialPage.getByRole('button', { name: 'create account' }).click();
	await expect(initialPage.locator('#lingo-app')).toContainText('Confirmation does not match', { ignoreCase: true });

	// long password
	await initialPage.reload();
	await initialPage.getByRole('row', { name: 'name:' }).getByRole('textbox').fill('John Doe');
	await initialPage.getByRole('row', { name: 'email:' }).nth(1).getByRole('textbox').fill(goodEmail);
	await initialPage.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill(longStr);
	await initialPage.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill('test-password-4567');
	await initialPage.getByRole('button', { name: 'create account' }).click();
	await expect(initialPage.locator('#lingo-app')).toContainText('Field "password" exceeds max length of 1000 characters.', { ignoreCase: true });

	// long password confirm
	await initialPage.reload();
	await initialPage.getByRole('row', { name: 'name:' }).getByRole('textbox').fill('John Doe');
	await initialPage.getByRole('row', { name: 'email:' }).nth(1).getByRole('textbox').fill(goodEmail);
	await initialPage.getByRole('row', { name: 'password:' }).nth(1).getByRole('textbox').fill('test-password-456');
	await initialPage.getByRole('row', { name: 'password confirm:' }).getByRole('textbox').fill(longStr);
	await initialPage.getByRole('button', { name: 'create account' }).click();
	await expect(initialPage.locator('#lingo-app')).toContainText('Field "password_confirm" exceeds max length of 1000 characters.', { ignoreCase: true });

	//
	// create account so we can create other items
	//

	const userContext = await browser.newContext();
	const page = await userContext.newPage();

	const { email, password } = await createAccount(page, host, uniqueId);
	await loginUser(page, host, email, password);
	
	//
	// profile validation errors
	//

	const userName = `user_${uniqueId}`
	await page.goto(`${host}/social/profile/yours`);

	// long username
	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(longStr);
	await page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor').fill('This is a bio.');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "username" is invalid: must be 25 characters or less and only contain letters, numbers, hyphens, underscores, periods, and tildes', { ignoreCase: true });

	// long bio
	await page.reload();
	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(userName);
	await page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor').fill(longRichText);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "bio" exceeds max length of 25000 characters.', { ignoreCase: true });

	// profile picture - invalid image file
	await page.reload();
	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(userName);
	await page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor').fill('This is a bio.');
	let profile_pic_row = page.getByRole('row', { name: 'profile picture:' });
	await profile_pic_row.locator('input[type="file"]').setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(page.locator('#lingo-app')).toContainText('File is missing an image track', { ignoreCase: true });

	// profile picture - too large image
	await page.reload();
	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(userName);
	await page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor').fill('This is a bio.');
	profile_pic_row = page.getByRole('row', { name: 'profile picture:' });
	await profile_pic_row.locator('input[type="file"]').setInputFiles('./tests/samples/large-image.tiff');
	await expect(page.locator('#lingo-app')).not.toContainText('success', { ignoreCase: true });
	await expect(page.locator('#lingo-app')).toContainText('failed', { ignoreCase: true });

	//
	// create profile so we can create other items
	//

	await createProfile(page, host, uniqueId);

	//
	// create invalid forum
	//

	// long topic
	await page.goto(`${host}/social/forum`);
	await page.getByRole('button', { name: 'create forum' }).click();
	await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(longStr);
	await page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor').fill('This is a description.');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "topic" exceeds max length of 1000 characters.', { ignoreCase: true });

	// long description
	await page.reload();
	await page.getByRole('button', { name: 'create forum' }).click();
	await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(`Valid Topic ${uniqueId}`);
	await page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor').fill(longRichText);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "description" exceeds max length of 25000 characters.', { ignoreCase: true });

	// too many tags
	await page.reload();
	await page.getByRole('button', { name: 'create forum' }).click();
	await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(`Valid Topic ${uniqueId}`);
	await page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor').fill('This is a description.');
	
	for (let i = 1; i < 12; i++) {
		await page.getByRole('textbox', { name: 'Enter text' }).fill(`tag-${i}`);
		await page.getByRole('textbox', { name: 'Enter text' }).press('Enter');
	}

	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "tags" exceeds max length of 10 items.', { ignoreCase: true });

	//
	// create forum and thread so we have at least 1 item to response to
	//

	await createForumAndThread(page, host, uniqueId);

	//
	// create invalid thread
	//

	await page.goto(`${host}/social/forum`);
	await page.locator('tr').nth(1).click();

	// long title
	await page.getByRole('button', { name: 'create thread' }).click();
	await page.getByRole('row', { name: 'title:' }).getByRole('textbox').fill(longStr);
	await page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor').fill('This is a message.');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "title" exceeds max length of 1000 characters.', { ignoreCase: true });

	// long message
	await page.reload();
	await page.getByRole('button', { name: 'create thread' }).click();
	await page.getByRole('row', { name: 'title:' }).getByRole('textbox').fill(`Valid Title ${uniqueId}`);
	await page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor').fill(longRichText);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "message" exceeds max length of 25000 characters.', { ignoreCase: true });

	
	
	//
	// create invalid reply
	//

	await page.goto(`${host}/social/forum`);
	await page.locator('tr').nth(1).click();
	await expect(page.locator('#lingo-app')).toContainText(':: forum ::', { ignoreCase: true });
	await page.locator('tr').nth(2).click();
	await expect(page.locator('#lingo-app')).toContainText(':: thread ::', { ignoreCase: true });

	// long message
	await page.locator('.rich-text-editor').fill(longRichText);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "message" exceeds max length of 25000 characters.', { ignoreCase: true });

});
