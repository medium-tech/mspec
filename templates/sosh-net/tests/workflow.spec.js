import { test } from './fixtures.js';
import { expect } from '@playwright/test';

//
// helper functions
//

async function createAccount(page, host, uniqueId) {
	const email = `workflow-${uniqueId}@example.com`;
	const password = `pw${uniqueId}`;

	await page.goto(`${host}/sosh-net/account`);
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
	await page.goto(`${host}/sosh-net/account`);
	await page.waitForSelector('#lingo-app');

	// login form is first on the page (before the create account form)
	await page.getByRole('row', { name: 'email: Email of the user' }).first().getByRole('textbox').fill(email);
	await page.getByRole('row', { name: 'password: show' }).first().getByRole('textbox').fill(password);
	await page.getByRole('button', { name: 'login' }).click();
	// after login the account details section becomes visible
	await expect(page.getByRole('heading', { name: ':: account details' })).toBeVisible({ timeout: 10000 });
}

async function createProfile(page, host, uniqueId) {
	await page.goto(`${host}/sosh-net/profile/yours`);
	// wait for auto-submit of get-current-user-profile to complete and show create form
	await expect(page.getByRole('heading', { name: ':: create profile' })).toBeVisible({ timeout: 10000 });

	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(`user_${uniqueId}`);
	await page.getByRole('row', { name: 'bio:' }).getByRole('textbox').fill(`Bio for workflow user ${uniqueId}`);
	// set profile_picture to -1 (no image selected)
	await page.getByRole('row', { name: 'profile picture:' }).locator('input[type="text"]').fill('-1');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success', { timeout: 10000 });
}

async function createForumAndThread(page, host, uniqueId) {
	await page.goto(`${host}/sosh-net/forum`);
	await page.waitForSelector('#lingo-app');

	// create a forum
	await page.getByRole('button', { name: 'create forum' }).click();
	await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(`Workflow Forum ${uniqueId}`);
	await page.getByRole('row', { name: 'description:' }).getByRole('textbox').fill(`Forum for workflow test ${uniqueId}`);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success', { timeout: 10000 });

	// navigate to the created forum via the 'view item' link
	await page.getByRole('link', { name: 'view item' }).click();
	await page.waitForSelector('#lingo-app');

	// create a thread in the forum
	await page.getByRole('button', { name: 'create thread' }).click();
	await page.getByRole('row', { name: 'title:' }).getByRole('textbox').fill(`Workflow Thread ${uniqueId}`);
	await page.getByRole('row', { name: 'message:' }).getByRole('textbox').fill(`Thread message for workflow test ${uniqueId}`);
	await page.getByRole('button', { name: 'Submit' }).click();
	// create-thread op shows 'view thread' link on success (not the generic 'success' text)
	await expect(page.getByRole('link', { name: 'view thread' })).toBeVisible({ timeout: 10000 });
}

async function logoutUser(page, host) {
	await page.goto(`${host}/sosh-net/account`);
	await page.waitForSelector('#lingo-app');
	await page.getByRole('button', { name: 'logout' }).click();
	// after logout the login section becomes visible again
	await expect(page.getByRole('heading', { name: ':: login' })).toBeVisible({ timeout: 10000 });
}

async function leaveReply(page, message) {
	// ':: add reply' section is at the bottom of the thread instance page
	await expect(page.getByRole('heading', { name: ':: add reply' })).toBeVisible({ timeout: 10000 });
	await page.getByRole('row', { name: 'message:' }).getByRole('textbox').fill(message);
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success', { timeout: 10000 });
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
	await expect(initialPage.locator('#lingo-app')).not.toContainText(':: sosh net');
	await expect(initialPage.locator('#lingo-app')).not.toContainText(':: available modules');

	//
	// sosh net main page
	//

	await initialPage.getByRole('link', { name: 'enter sosh net' }).click();
	await expect(initialPage.locator('h1')).toContainText('shosh net');
	await expect(initialPage.getByRole('link', { name: 'mtech' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'sosh-net' })).toBeVisible();
	await expect(initialPage.locator('h2')).toContainText(':: the network');
	await expect(initialPage.getByRole('link', { name: 'front page' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'profiles' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'forums' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'account' })).toBeVisible();
	await expect(initialPage.locator('#lingo-app')).toContainText('this is sosh net.');
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
		await page.goto(`${host}/sosh-net/profile`);
		await page.waitForSelector('tr.list-selecting', { timeout: 10000 });
		await page.locator('tr.list-selecting').first().click();
		await page.waitForSelector('#lingo-app');

		// navigate to forums and click on the first forum
		await page.goto(`${host}/sosh-net/forum`);
		await page.waitForSelector('tr.list-selecting', { timeout: 10000 });
		await page.locator('tr.list-selecting').first().click();

		// wait for the forum instance to load its thread list
		await page.waitForSelector('tr.list-selecting', { timeout: 10000 });
		// click on the first thread in the forum
		await page.locator('tr.list-selecting').first().click();

		// leave a reply on the thread
		await leaveReply(page, `Reply from workflow user ${user.email}`);

		// logout
		await logoutUser(page, host);

		// --- error checks when not logged in ---

		// profile list requires login
		await page.goto(`${host}/sosh-net/profile`);
		await expect(page.locator('#lingo-app')).toContainText('Error: Not logged in', { timeout: 10000 });

		// profile instance requires login
		await page.goto(`${host}/sosh-net/profile/1`);
		await expect(page.locator('#lingo-app')).toContainText('Error: Not logged in', { timeout: 10000 });

		// forum list requires login
		await page.goto(`${host}/sosh-net/forum`);
		await expect(page.locator('#lingo-app')).toContainText('Error: Not logged in', { timeout: 10000 });

		// forum instance op returns a server error when not logged in
		await page.goto(`${host}/sosh-net/forum/1`);
		await expect(page.locator('#lingo-app')).toContainText('Contact support or check logs for details', { timeout: 10000 });

		// thread instance op returns a server error when not logged in
		await page.goto(`${host}/sosh-net/thread/1`);
		await expect(page.locator('#lingo-app')).toContainText('Contact support or check logs for details', { timeout: 10000 });

		await userContext.close();
	}
});

