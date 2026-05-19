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
	const editor = await page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor')
	editor.fill(`Forum for workflow test ${uniqueId}`);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success', { timeout: 10000 });

	// navigate to the created forum via the 'view item' link
	await page.getByRole('link', { name: 'view item' }).click();
	await page.waitForSelector('#lingo-app');

	// create a thread in the forum
	await page.getByRole('button', { name: 'create thread' }).click();
	await page.getByRole('row', { name: 'title:' }).getByRole('textbox').fill(`Workflow Thread ${uniqueId}`);
	await page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor').fill(`Thread message for workflow test ${uniqueId}`);
	await page.getByRole('button', { name: 'Submit' }).click();
	// create-thread op shows 'view thread' link on success (not the generic 'success' text)
	await expect(page.getByRole('link', { name: 'view thread' })).toBeVisible({ timeout: 10000 });
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
	await initialContext.close();

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
	}
});

test('test navigation links', async ({ browser, crudEnv }) => {
	const host = crudEnv.host;

	const uniqueId = Date.now() * 1000;
	const userContext = await browser.newContext();
	const page = await userContext.newPage();

	const { email, password } = await createAccount(page, host, uniqueId);
	await loginUser(page, host, email, password);
	await createProfile(page, host, uniqueId);
	await createForumAndThread(page, host, uniqueId);

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

	// view forum breadcrumbs
	await page.goto(`${host}/social/forum`);
	await expect(page.locator('h2')).toContainText(':: search forums');
	await page.locator('tr').nth(1).click();

	await expect(page.locator('h1')).toContainText(':: forum ::');
	await page.getByRole('link').nth(3).click();

	await expect(page.locator('h1')).toContainText(':: forum ::');
	await page.getByRole('link', { name: 'forum' }).click();
	await expect(page.locator('h2')).toContainText(':: search forums');
	
	await page.goto(`${host}/social/forum`);
	await expect(page.locator('h2')).toContainText(':: search forums');
	await page.locator('tr').nth(1).click();
	await expect(page.locator('h1')).toContainText(':: forum ::');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h2')).toContainText(':: the network');
	await page.goto(`${host}/social/forum`);
	await expect(page.locator('h2')).toContainText(':: search forums');
	await page.locator('tr').nth(1).click();
	await expect(page.locator('h1')).toContainText(':: forum ::');
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText('medium tech');

	// view thread breadcrumbs
	await page.goto(`${host}/social/thread/1`);
	await expect(page.locator('h1')).toContainText(':: thread ::');
	await page.getByRole('link').nth(4).click();
	await expect(page.locator('h1')).toContainText(':: forum ::');

	await page.goto(`${host}/social/thread/1`);
	await page.getByRole('link').nth(3).click();
	await expect(page.locator('h1')).toContainText(':: forum ::');
	
	await page.goto(`${host}/social/thread/1`);
	await expect(page.locator('h1')).toContainText(':: thread ::');
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h2')).toContainText(':: the network');
	await page.goto(`${host}/social/thread/1`);
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