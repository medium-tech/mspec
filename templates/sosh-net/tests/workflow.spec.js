import { test } from './fixtures.js';
import { expect } from '@playwright/test';

//
// helper functions
//

async function createAccount(page, host, uniqueId) {
	const email = `workflow-${uniqueId}@example.com`;
	const password = `pw${uniqueId}`;

	await page.goto(`${host}/social/account`);
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
	await page.goto(`${host}/social/account`);
	await page.waitForSelector('#lingo-app');

	// login form is first on the page (before the create account form)
	await page.getByRole('row', { name: 'email: Email of the user' }).first().getByRole('textbox').fill(email);
	await page.getByRole('row', { name: 'password: show' }).first().getByRole('textbox').fill(password);
	await page.getByRole('button', { name: 'login' }).click();

	await expect(page.getByRole('heading', { name: ':: login' })).not.toBeVisible({ timeout: 10000 });
	await expect(page.getByRole('button', { name: 'logout' })).toBeVisible({ timeout: 10000 });
}
	
async function createProfile(page, host, uniqueId) {
	await page.goto(`${host}/social/profile/yours`);
	await expect(page.getByRole('heading', { name: ':: create your profile' })).toBeVisible({ timeout: 10000 });

	const username = `user_${uniqueId}`;
	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(username);
	const editor = page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor');
	await editor.fill(`Bio for workflow user ${uniqueId}`);

	const profile_pic_row = page.getByRole('row', { name: 'profile picture:' });
	await profile_pic_row.locator('input[type="file"]').setInputFiles('./tests/samples/splash-low.jpg');
	await expect(page.locator('#lingo-app')).not.toContainText('Uploading file...');
	await expect(page.locator('#lingo-app')).toContainText('File uploaded successfully!');
	await expect(page.locator('#lingo-app')).not.toContainText('error');
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Success', { timeout: 10000 });

	return { username };
}

async function createForumAndThread(page, host, uniqueId) {
	await page.goto(`${host}/social/forum`);
	await page.waitForSelector('#lingo-app');

	const forumTopic = `Workflow Forum ${uniqueId}`;
	const threadTitle = `Workflow Thread ${uniqueId}`;

	// create a forum
	await page.getByRole('button', { name: 'create forum' }).click();
	await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(forumTopic);
	const editor = await page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor');
	await editor.fill(`Forum for workflow test ${uniqueId}`);
	await expect(editor).toContainText(`Forum for workflow test ${uniqueId}`, { timeout: 10000 });
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
	await page.getByRole('row', { name: 'title:' }).getByRole('textbox').fill(threadTitle);
	await page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor').fill(`Thread message for workflow test ${uniqueId}`);
	await expect(page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor')).toContainText(`Thread message for workflow test ${uniqueId}`, { timeout: 10000 });
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

	return { forumId, forumTopic, threadId, threadTitle };
}

async function logoutUser(page, host) {
	await page.goto(`${host}/social/account`);
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
	await expect(page.locator('div.rich-text-editor')).toContainText(message, { timeout: 10000 });
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
	await expect(initialPage.getByRole('heading')).toContainText(':: medium tech');

	// confirm front page does not have protocol_mode content
	await expect(initialPage.locator('#lingo-app')).not.toContainText('available modules');

	//
	// social main page
	//

	await initialPage.getByRole('link', { name: 'social network' }).click();
	await expect(initialPage.locator('h1')).toContainText(':: mtech social network');
	await expect(initialPage.getByRole('link', { name: 'mtech' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'social' })).toBeVisible();
	
	await expect(initialPage.getByRole('link', { name: 'profiles' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'forums' })).toBeVisible();
	await expect(initialPage.getByRole('link', { name: 'account' })).toBeVisible();

	await expect(initialPage.locator('#lingo-app')).toContainText('where do you want to go?');
	// await initialContext.close();

	//
	// phase 1: create 2 users with profiles, first user will create a forum and thread for interacting with
	//

	const users = [];
	let forumId = null, forumTopic = null, threadId = null, threadTitle = null;

	for (let i = 0; i < 2; i++) {
		// multiply by 1000 and add i to guarantee uniqueness even within the same millisecond
		const uniqueId = Date.now() * 1000 + i;
		const userContext = await browser.newContext();
		const page = await userContext.newPage();

		const { email, password } = await createAccount(page, host, uniqueId);
		await loginUser(page, host, email, password);
		const { username } = await createProfile(page, host, uniqueId);
		
		
		if(i === 0){
			({ forumId, forumTopic, threadId, threadTitle } = await createForumAndThread(page, host, uniqueId));
		}
		await logoutUser(page, host);

		await userContext.close();
		users.push({ email, password, username });
	}

	//
	// phase 2: each user logs in, interacts, logs out, then checks auth errors
	//

	let userIndex = 0;
	let userLoginPages = [];

	for (const user of users) {
		const userContext = await browser.newContext();
		const page = await userContext.newPage();
		userLoginPages.push(page);

		//
		// user account
		//

		// login
		await loginUser(page, host, user.email, user.password);

		// check account page
		await page.goto(`${host}/social`);
		await page.getByRole('link', { name: 'account' }).click();
		await expect(page.locator('h1')).toContainText(':: account details', { timeout: 10000 });
		await expect(page.locator('#lingo-app')).toContainText(user.email, { timeout: 10000 });

		// navigate to your profile page
		await page.getByRole('link', { name: 'create or edit' }).click();
		await expect(page.locator('h1')).toContainText(':: edit your profile', { timeout: 10000 });
		await expect(page.locator('#lingo-app')).toContainText(user.username, { timeout: 10000 });

		// navigate to profile instance page via 'view public profile' link
		await page.getByRole('link', { name: 'view public profile' }).click();
		await expect(page.locator('h1')).toContainText(':: profile ::', { timeout: 10000 });
		await expect(page.locator('#lingo-app')).toContainText(user.username, { timeout: 10000 });

		//
		// browse public content
		//

		// if tests are running parallel these may or may not be the forums that the user created in this test
		// but thats not important for testing browse functionality

		// navigate to profiles page and click on the first profile
		await page.getByRole('link', { name: 'profile', exact: true }).click();
		await page.waitForSelector('tr.list-selecting', { timeout: 10000 });
		await page.locator('tr.list-selecting').first().click();
		await page.waitForSelector('#lingo-app');
		await expect(page.locator('h1')).toContainText(':: profile ::', { timeout: 10000 });

		// navigate to forums and click on the first forum
		await page.getByRole('link', { name: 'social' }).click();
		await page.getByRole('link', { name: 'forums' }).click();
		
		await expect(page.locator('h1')).toContainText(`:: forums`, { timeout: 10000 });
		await page.locator('tr').nth(1).click();
		await expect(page.locator('h3')).toContainText(':: threads in forum', { timeout: 10000 });

		// click on the first thread in the forum
		await page.locator('tr.list-selecting').first().click();
		await page.locator('tr').nth(1).click();
		await expect(page.locator('h3')).toContainText(':: replies to thread', { timeout: 10000 });

		//
		// forum
		//

		await page.goto(`${host}/social/forum/${forumId}`);
		await expect(page.locator('h1')).toContainText(`:: ${forumTopic}`, { timeout: 10000 });
		if (userIndex === 0) {
			await expect(page.locator('#lingo-app')).toContainText('(you own this forum)', { timeout: 10000 });
			await expect(page.getByRole('button', { name: 'open editor' })).toBeVisible({ timeout: 10000 });
		}else{
			await expect(page.locator('#lingo-app')).not.toContainText('(you own this forum)', { timeout: 10000 });
			await expect(page.getByRole('button', { name: 'open editor' })).not.toBeVisible({ timeout: 10000 });
		}

		//
		// thread main post
		//

		/*

		Reaction data separation. We will be reacting to the main post and also a reply, to maintain separate state we use these rules
		- for permanent reactions that we want to stay in place for the next user to see we will use 👍 for the main post and ❤️ for the reply
		- to test changing and removing reactions, we will use 🔥 and 😢

		for testing we can always expect 🔥 and 😢 to have count 1 anywhere on the page (main post or replies)
		and we can also have deterministic counts for main post and reply by isolating them to 👍 and ❤️

		*/

		await page.goto(`${host}/social/thread/${threadId}`);
		await expect(page.locator('h1')).toContainText(`:: ${threadTitle}`, { timeout: 10000 });

		// expect a link with text '@<username>' of userIndex 0 who created <threadId>
		await page.getByRole('link', { name: `@${users[0].username}` }).first().click();
		await expect(page.locator('h1')).toContainText(':: profile ::', { timeout: 10000 });
		await expect(page.locator('#lingo-app')).toContainText(users[0].username, { timeout: 10000 });

		// back to thread
		await page.goBack();
		await expect(page.locator('h1')).toContainText(`:: ${threadTitle}`, { timeout: 10000 });

		// if userIndex is 0, expect text "(you own this thread)" and button with text "open editor"
		if (userIndex === 0) {
			await expect(page.locator('#lingo-app')).toContainText('(you own this thread)', { timeout: 10000 });
			await expect(page.getByRole('button', { name: 'open editor' })).toBeVisible({ timeout: 10000 });
		}else{
			await expect(page.locator('#lingo-app')).not.toContainText('(you own this thread)', { timeout: 10000 });
			await expect(page.getByRole('button', { name: 'open editor' })).not.toBeVisible({ timeout: 10000 });
		}

		// create initial reaction on the main post
		await page.getByRole('button', { name: '🔥' }).first().click();
		await expect(page.locator('#lingo-app')).toContainText(`🔥x1`, { timeout: 10000 });
		await expect(page.getByRole('button', { name: 'unreact 🔥' })).toBeVisible({ timeout: 10000 });

		// change reaction to sad face
		await page.getByRole('button', { name: '😢' }).first().click();
		await expect(page.locator('#lingo-app')).not.toContainText(`🔥x1`, { timeout: 10000 });
		await expect(page.locator('#lingo-app')).toContainText(`😢x1`, { timeout: 10000 });
		
		// remove reaction
		await page.getByRole('button', { name: 'unreact 😢' }).first().click();
		await expect(page.locator('#lingo-app')).not.toContainText(`🔥x1`, { timeout: 10000 });
		await expect(page.locator('#lingo-app')).not.toContainText(`😢x1`, { timeout: 10000 });
		await expect(page.getByRole('button', { name: 'unreact 😢' })).not.toBeVisible({ timeout: 10000 });

		// add another reaction to leave in place for the next user to see
		await page.getByRole('button', { name: '👍' }).first().click();
		const emojiThreadCount = userIndex + 1;
		await expect(page.locator('#lingo-app')).toContainText(`👍x${emojiThreadCount}`, { timeout: 10000 });

		//
		// reply to thread
		//

		const replyMessage = `This is a reply from user ${user.username}`;
		await leaveReply(page, replyMessage);
		await page.getByRole('button', { name: 'refresh' }).nth(userIndex).click();		// there are 2 refresh buttons and we test them both
																						// userIndex 0 tests the first and userIndex 1 tests the second
		
		// there should now be a link to user 0's profile on the main thread and reply
		await expect(page.getByRole('link', { name: `@${users[0].username}` })).toHaveCount(2, { timeout: 10000 });
		// expect exactly 1 span element with text "(your reply)" and 1 button with text "delete"
		await expect(page.locator('span', { hasText: '(your reply)' })).toHaveCount(1, { timeout: 10000 });
		await expect(page.getByRole('button', { name: 'delete' })).toHaveCount(1, { timeout: 10000 });

		// navigate to reply author's profile and back to thread
		await page.getByRole('link', { name: `@${users[0].username}` }).nth(1).click();
		await expect(page.locator('h1')).toContainText(':: profile ::', { timeout: 10000 });
		await expect(page.locator('#lingo-app')).toContainText(users[0].username, { timeout: 10000 });
		await page.goBack();
		await expect(page.locator('h1')).toContainText(`:: ${threadTitle}`, { timeout: 10000 });

		if (userIndex === 1) {
			await expect(page.getByRole('link', { name: `@${users[1].username}` })).toBeVisible({ timeout: 10000 });
			await page.getByRole('link', { name: `@${users[1].username}` }).click();
			await expect(page.locator('h1')).toContainText(':: profile ::', { timeout: 10000 });
			await expect(page.locator('#lingo-app')).toContainText(users[1].username, { timeout: 10000 });
			await page.goBack();
			await expect(page.locator('h1')).toContainText(`:: ${threadTitle}`, { timeout: 10000 });
		}

		//
		// react to reply
		//

		// create initial reaction on the main post
		await page.getByRole('button', { name: '🔥' }).nth(1).click();
		await expect(page.getByRole('button', { name: 'unreact 🔥' })).toBeVisible({ timeout: 10000 });
		await page.reload();	// reload page because reply reactions are not in real time (yet)
		await expect(page.locator('#lingo-app')).toContainText(`🔥x1`, { timeout: 10000 });
		await expect(page.getByRole('button', { name: 'unreact 🔥' })).toBeVisible({ timeout: 10000 });

		// change reaction to sad face
		await page.getByRole('button', { name: '😢' }).nth(1).click();
		await expect(page.getByRole('button', { name: 'unreact 😢' })).toBeVisible({ timeout: 10000 });
		await page.reload();	// reload page because reply reactions are not in real time (yet)
		await expect(page.locator('#lingo-app')).not.toContainText(`🔥x1`, { timeout: 10000 });
		await expect(page.locator('#lingo-app')).toContainText(`😢x1`, { timeout: 10000 });
		
		// remove reaction
		await page.getByRole('button', { name: 'unreact 😢' }).click();
		await expect(page.getByRole('button', { name: 'unreact 😢' })).not.toBeVisible({ timeout: 10000 });
		await page.reload();	// reload page because reply reactions are not in real time (yet)
		await expect(page.locator('#lingo-app')).not.toContainText(`🔥x1`, { timeout: 10000 });
		await expect(page.locator('#lingo-app')).not.toContainText(`😢x1`, { timeout: 10000 });
		await expect(page.getByRole('button', { name: 'unreact 😢' })).not.toBeVisible({ timeout: 10000 });

		// add another reaction to leave in place for the next user to see
		await page.getByRole('button', { name: '❤️' }).nth(userIndex + 1).click();									// we click on nth(userIndex + 1) because for userIndex 0 to reply to their own reply they need
		await expect(page.getByRole('button', { name: 'unreact ❤️' })).toBeVisible({ timeout: 10000 });				// to click on the 2nd ❤️ button on the page, but when userIndex 1 replies their reply will
		await page.reload();	// reload page because reply reactions are not in real time (yet)					// go above userIndex 0's reply, so now they will click the 3rd ❤️ button on the page to react to userIndex 0's reply
		const emojiReplyCount = userIndex + 1;
		await expect(page.locator('#lingo-app')).toContainText(`❤️x${emojiReplyCount}`, { timeout: 10000 });
		await expect(page.getByRole('button', { name: 'unreact ❤️' })).toBeVisible({ timeout: 10000 });

		userIndex++;
	}

	//
	// mutate data
	//

	const user0Page = userLoginPages[0];
	const user1Page = userLoginPages[1];
	const threadUrl = `${host}/social/thread/${threadId}`;

	// delete user 1 reply //

	await user1Page.goto(threadUrl);
	await user1Page.getByRole('button', { name: 'delete' }).click();
	await expect(user1Page.locator('#lingo-app')).toContainText('Are you sure you want to delete this model instance? This action cannot be undone.', { timeout: 10000 });
	await user1Page.getByRole('button', { name: 'cancel' }).click();
	await expect(user1Page.locator('#lingo-app')).not.toContainText('Are you sure you want to delete this model instance? This action cannot be undone.', { timeout: 10000 });
	await user1Page.getByRole('button', { name: 'delete' }).click();
	await user1Page.getByRole('button', { name: 'confirm delete' }).click();
	await expect(user1Page.locator('#lingo-app')).toContainText('item deleted successfully', { timeout: 10000 });
	await user1Page.getByRole('button', { name: 'refresh' }).first().click();
	await expect(user1Page.getByRole('link', { name: `@${users[1].username}` })).not.toBeVisible({ timeout: 10000 });

	// edit forum //

	const newForumTopic = `${forumTopic} (edited)`;
	const newForumDescription = 'I have changed the description of this forum!';

	// change data
	await user0Page.goto(`${host}/social/forum/${forumId}`);
	await expect(user0Page.locator('h1')).toContainText(`:: ${forumTopic}`, { timeout: 10000 });
	await user0Page.getByRole('button', { name: 'open editor' }).click();
	await user0Page.getByRole('button', { name: 'edit', exact: true }).click();
	await user0Page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(newForumTopic);
	const editor = await user0Page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor');
	await editor.fill(newForumDescription);
	await expect(editor).toContainText(newForumDescription, { timeout: 10000 });

	// submit changes
	await expect(user0Page.locator('#lingo-app')).toContainText('(modified)', { timeout: 10000 });
	await user0Page.getByRole('button', { name: 'Submit' }).click();
	await expect(user0Page.locator('#lingo-app')).toContainText('edited', { timeout: 10000 });
	await user0Page.getByRole('button', { name: 'close editor' }).first().click();

	// confirm changes
	await user0Page.waitForLoadState('networkidle');
	await expect(user0Page.locator('h1')).toContainText(`:: ${newForumTopic}`, { timeout: 10000 });
	await expect(user0Page.locator('#lingo-app')).toContainText(newForumDescription, { timeout: 10000 });
	await expect(user0Page.getByRole('button', { name: 'close editor' })).not.toBeVisible({ timeout: 10000 });
	await expect(user0Page.getByRole('button', { name: 'open editor' })).toBeVisible({ timeout: 10000 });

	// edit thread //

	// change data
	const newThreadTitle = `${threadTitle} (edited)`;
	const newThreadMessage = 'I have changed the message of this thread!';
	await user0Page.goto(`${host}/social/thread/${threadId}`);
	await expect(user0Page.locator('h1')).toContainText(`:: ${threadTitle}`, { timeout: 10000 });
	await user0Page.getByRole('button', { name: 'open editor' }).click();
	await user0Page.getByRole('row', { name: 'title:' }).getByRole('textbox').fill(newThreadTitle);
	await user0Page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor').first().fill(newThreadMessage);
	await expect(user0Page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor').first()).toContainText(newThreadMessage, { timeout: 10000 });

	// submit and confirm changes
	await user0Page.getByRole('button', { name: 'Submit' }).first().click();
	await user0Page.waitForLoadState('networkidle');
	await expect(user0Page.locator('h1')).toContainText(`:: ${newThreadTitle}`, { timeout: 10000 });
	await expect(user0Page.locator('#lingo-app')).toContainText(newThreadMessage, { timeout: 10000 });

	await user1Page.close();
	await user0Page.close();
});

test('test logged out session cannot view items', async ({ browser, crudEnv }) => {

	//
	// seed data so there is at least a forum and thread to navigate to
	//

	const host = crudEnv.host;

	const uniqueId = Date.now() * 1000;
	const initialContext = await browser.newContext();
	const page = await initialContext.newPage();
	const user = await createAccount(page, host, uniqueId);
	await loginUser(page, host, user.email, user.password);
	await createProfile(page, host, uniqueId);
	const { forumId, forumTopic, threadId, threadTitle } = await createForumAndThread(page, host, uniqueId);

	//
	// error checks when not logged in
	// 

	// logout
	await logoutUser(page, host);

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
	await page.goto(`${host}/social/forum/${forumId}`);
	await expect(page.locator('#lingo-app')).toContainText('Contact support or check logs for details', { timeout: 10000, ignoreCase: true });

	// thread instance op returns a server error when not logged in
	await page.goto(`${host}/social/thread/${threadId}`);
	await expect(page.locator('#lingo-app')).toContainText('Contact support or check logs for details', { timeout: 10000, ignoreCase: true });

	await initialContext.close();

});

test('test require profile to create items', async ({ browser, crudEnv }) => {

	//
	// seed data so there is at least a forum and thread to navigate to
	//

	const host = crudEnv.host;

	const uniqueSeedId = Date.now() * 1000;
	const seedContext = await browser.newContext();
	const seedPage = await seedContext.newPage();
	const seedUser = await createAccount(seedPage, host, uniqueSeedId);
	await loginUser(seedPage, host, seedUser.email, seedUser.password);
	await createProfile(seedPage, host, uniqueSeedId);
	await createForumAndThread(seedPage, host, uniqueSeedId);

	//
	// confirm user must have profile to create forums/threads/replies
	//

	// create user w/o profile
	const userContext = await browser.newContext();
	const page = await userContext.newPage();
	await page.goto(host);
	const uniqueId = Date.now() * 1000;
	const user = await createAccount(page, host, uniqueId);
	await loginUser(page, host, user.email, user.password);

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
	
	await page.locator('.rich-text-editor').fill('Because I don\'t have a profile!');
	await expect(page.locator('.rich-text-editor')).toContainText('Because I don\'t have a profile!', { timeout: 10000 });
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.getByRole('table')).toContainText('error');
	await expect(page.getByRole('table')).toContainText('You must have a profile to create items');

	// cannot reply to thread without profile
	await page.goto(`${host}/social/forum`);
	await page.locator('tr').nth(1).click();
	await page.locator('tr').nth(2).click();
	await page.locator('.rich-text-editor').fill('I can\'t reply without a profile!');
	await expect(page.locator('.rich-text-editor')).toContainText('I can\'t reply without a profile!', { timeout: 10000 });
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('error');
	await expect(page.locator('#lingo-app')).toContainText('You must have a profile to create items');

});

test('test navigation links', async ({ browser, crudEnv }) => {

	//
	// seed data so there is at least a forum and thread to navigate to
	//

	const host = crudEnv.host;

	const uniqueId = Date.now() * 1000;
	const userContext = await browser.newContext();
	const page = await userContext.newPage();

	const { email, password } = await createAccount(page, host, uniqueId);
	await loginUser(page, host, email, password);
	await createProfile(page, host, uniqueId);
	const { forumId, forumTopic, threadId, threadTitle } = await createForumAndThread(page, host, uniqueId);

	//
	// constants
	//

	const indexUrl = host;
	const socialUrl = `${host}/social`;
	const profilesUrl = `${host}/social/profile`;
	const yourProfileUrl = `${host}/social/profile/yours`;
	const forumsUrl = `${host}/social/forum`;
	const forumInstanceUrl = `${host}/social/forum/${forumId}`;
	const threadInstanceUrl = `${host}/social/thread/${threadId}`;
	const accountUrl = `${host}/social/account`;

	const indexPageHeading = ':: medium tech';
	const socialModuleHeading = ':: mtech social network';
	const accountPageHeading = ':: account details';
	const profilesPageHeading = ':: profiles';
	const profileInstanceHeading = ':: profile ::';
	const yourProfileHeading = ':: edit your profile';
	const forumsPageHeading = ':: forums';
	const forumInstanceHeading = `:: ${forumTopic}`;
	const threadInstanceHeading = `:: ${threadTitle}`;

	//
	// index page
	//

	await page.goto(indexUrl);
	await expect(page.getByRole('heading')).toContainText(indexPageHeading);

	// breadcrumb link to self //
	await page.getByRole('link', { name: 'mtech' }).click();
	await page.waitForLoadState('networkidle');
	await expect(page.getByRole('heading')).toContainText(indexPageHeading);

	// menu //
	await page.goto(indexUrl);
	await page.getByRole('link', { name: 'social network' }).click();
	await expect(page.getByRole('heading')).toContainText(socialModuleHeading);

	await page.goto(indexUrl);
	await page.getByRole('link', { name: 'account' }).click();
	await expect(page.locator('h1')).toContainText(accountPageHeading);

	//
	// social network index page
	//

	await page.goto(socialUrl);
	await expect(page.locator('h1')).toContainText(socialModuleHeading);

	// breadcrumbs //
	await page.getByRole('link', { name: 'social' }).click();
	await page.waitForLoadState('networkidle');
	await expect(page.locator('h1')).toContainText(socialModuleHeading);

	await page.goto(socialUrl);
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText(indexPageHeading);

	// menu //
	await page.goto(socialUrl);
	await page.getByRole('link', { name: 'profiles' }).click();
	await expect(page.locator('h1')).toContainText(profilesPageHeading);

	await page.goto(socialUrl);
	await page.getByRole('link', { name: 'forums' }).click();
	await expect(page.locator('h1')).toContainText(forumsPageHeading);

	await page.goto(socialUrl);
	await page.getByRole('link', { name: 'account' }).click();
	await expect(page.locator('h1')).toContainText(accountPageHeading);

	//
	// your profile
	// 

	await page.goto(yourProfileUrl);
	await expect(page.getByRole('heading')).toContainText(yourProfileHeading);

	await page.getByRole('link', { name: 'view public profile' }).click();
	await expect(page.getByRole('heading')).toContainText(profileInstanceHeading);
	
	// breadcrumbs //
	await page.goto(yourProfileUrl);
	await page.getByRole('link', { name: 'yours' }).click();
	await page.waitForLoadState('networkidle');
	await expect(page.getByRole('heading')).toContainText(yourProfileHeading);

	await page.getByRole('link', { name: 'profile', exact: true }).click();
	await expect(page.locator('h1')).toContainText(profilesPageHeading);
	
	await page.goto(yourProfileUrl);
	await expect(page.getByRole('heading')).toContainText(yourProfileHeading);
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.getByRole('heading')).toContainText(socialModuleHeading);

	await page.goto(yourProfileUrl);
	await expect(page.getByRole('heading')).toContainText(yourProfileHeading);
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText(indexPageHeading);

	//
	// profiles
	//

	await page.goto(profilesUrl);
	await expect(page.getByRole('heading')).toContainText(profilesPageHeading);

	// breadcrumbs //
	await page.getByRole('link', { name: 'profile', exact: true }).click();
	await page.waitForLoadState('networkidle');
	await expect(page.getByRole('heading')).toContainText(profilesPageHeading);

	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.getByRole('heading')).toContainText(socialModuleHeading);
	
	await page.goto(profilesUrl);
	await expect(page.getByRole('heading')).toContainText(profilesPageHeading);
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText(indexPageHeading);

	//
	// forums
	//

	await page.goto(forumsUrl);
	await expect(page.getByRole('heading')).toContainText(forumsPageHeading);

	// breadcrumbs //
	await page.getByRole('link', { name: 'forum' }).click();
	await page.waitForLoadState('networkidle');
	await expect(page.getByRole('heading')).toContainText(forumsPageHeading);

	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.getByRole('heading')).toContainText(socialModuleHeading);
	
	await page.goto(forumsUrl);
	await expect(page.getByRole('heading')).toContainText(forumsPageHeading);
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.getByRole('heading')).toContainText(indexPageHeading);

	//
	// forum instance
	//

	await page.goto(forumInstanceUrl);
	await expect(page.locator('h1')).toContainText(forumInstanceHeading);

	// breadcrumbs //
	await page.getByRole('link', { name: 'forums' }).click();
	await page.waitForLoadState('networkidle');
	await expect(page.locator('h1')).toContainText(forumsPageHeading);

	await page.goto(forumInstanceUrl);
	await expect(page.locator('h1')).toContainText(forumInstanceHeading);
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h1')).toContainText(socialModuleHeading);
	
	await page.goto(forumInstanceUrl);
	await expect(page.locator('h1')).toContainText(forumInstanceHeading);
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.locator('h1')).toContainText(indexPageHeading);

	//
	// thread instance
	//

	await page.goto(threadInstanceUrl);
	await expect(page.locator('h1')).toContainText(threadInstanceHeading);

	// breadcrumbs //
	await page.getByRole('link', { name: forumTopic, exact: true }).click();
	await expect(page.locator('h1')).toContainText(forumInstanceHeading);

	await page.goto(threadInstanceUrl);
	await expect(page.locator('h1')).toContainText(threadInstanceHeading);
	await page.getByRole('link', { name: 'forums' }).click();
	await expect(page.locator('h1')).toContainText(forumsPageHeading);

	await page.goto(threadInstanceUrl);
	await expect(page.locator('h1')).toContainText(threadInstanceHeading);
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h1')).toContainText(socialModuleHeading);
	
	await page.goto(threadInstanceUrl);
	await expect(page.locator('h1')).toContainText(threadInstanceHeading);
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.locator('h1')).toContainText(indexPageHeading);

	//
	// account page
	//

	await page.goto(accountUrl);
	await expect(page.locator('h1')).toContainText(accountPageHeading);

	// breadcrumbs //
	await page.getByRole('link', { name: 'account' }).click();
	await page.waitForLoadState('networkidle');
	await expect(page.locator('h1')).toContainText(accountPageHeading);

	await page.goto(accountUrl);
	await expect(page.locator('h1')).toContainText(accountPageHeading);
	await page.getByRole('link', { name: 'social' }).click();
	await expect(page.locator('h1')).toContainText(socialModuleHeading);
	
	await page.goto(accountUrl);
	await expect(page.locator('h1')).toContainText(accountPageHeading);
	await page.getByRole('link', { name: 'mtech' }).click();
	await expect(page.locator('h1')).toContainText(indexPageHeading);

	// other links //
	await page.goto(accountUrl);
	await expect(page.locator('h1')).toContainText(accountPageHeading);
	await page.getByRole('link', { name: 'get a verification code' }).click();
	await expect(page.locator('h1')).toContainText(':: start-email-verification');

	await page.goto(accountUrl);
	await expect(page.locator('h1')).toContainText(accountPageHeading);
	await page.getByRole('link', { name: 'verify a code you received' }).click();
	await expect(page.locator('h1')).toContainText(':: verify-email-address');

	await page.goto(accountUrl);
	await expect(page.locator('h1')).toContainText(accountPageHeading);
	await page.getByRole('link', { name: 'create or edit' }).click();
	await expect(page.locator('h1')).toContainText(':: edit your profile');
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
	await page.goto(`${host}/social/account`);
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
	await page.goto(`${host}/social/account`);
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
	await initialPage.goto(host);
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
	await expect(page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor')).toContainText('This is a bio.', { timeout: 10000 });
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "username" is invalid: must be 25 characters or less and only contain letters, numbers, hyphens, underscores, periods, and tildes', { ignoreCase: true });

	// long bio - rich text tests are not reliable
	// await page.reload();
	// await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(userName);
	// await page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor').fill(longRichText);
	// await expect(page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor')).toContainText(longRichText.slice(0, 15), { timeout: 10000 });
	// await page.getByRole('button', { name: 'Submit' }).click();
	// await expect(page.locator('#lingo-app')).toContainText('Field "bio" exceeds max length of 25000 characters.', { ignoreCase: true });

	// profile picture - invalid image file
	await page.reload();
	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(userName);
	await page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor').fill('This is a bio.');
	await expect(page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor')).toContainText('This is a bio.', { timeout: 10000 });
	let profile_pic_row = page.getByRole('row', { name: 'profile picture:' });
	await profile_pic_row.locator('input[type="file"]').setInputFiles('./tests/samples/lorem-document.pdf');
	await expect(page.locator('#lingo-app')).toContainText('File is missing an image track', { ignoreCase: true });

	// profile picture - too large image
	await page.reload();
	await page.getByRole('row', { name: 'username:' }).getByRole('textbox').fill(userName);
	await page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor').fill('This is a bio.');
	await expect(page.getByRole('row', { name: 'bio:' }).locator('div.rich-text-editor')).toContainText('This is a bio.', { timeout: 10000 });
	profile_pic_row = page.getByRole('row', { name: 'profile picture:' });
	await profile_pic_row.locator('input[type="file"]').setInputFiles('./tests/samples/large-image.tiff');
	await expect(page.locator('#lingo-app')).not.toContainText('success', { ignoreCase: true });

	// case insensitive regix to find "fail" or "error"
	await expect(page.locator('#lingo-app')).toContainText(/(fail|error)/i, { ignoreCase: true });

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
	await expect(page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor')).toContainText('This is a description.', { timeout: 10000 });
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "topic" exceeds max length of 1000 characters.', { ignoreCase: true });

	// long description - rich text tests are not reliable
	// await page.reload();
	// await page.getByRole('button', { name: 'create forum' }).click();
	// await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(`Valid Topic ${uniqueId}`);
	// await page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor').fill(longRichText);
	// await expect(page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor')).toContainText(longRichText.slice(0, 20), { timeout: 10000 });
	// await page.getByRole('button', { name: 'Submit' }).click();
	// await expect(page.locator('#lingo-app')).toContainText('Field "description" exceeds max length of 25000 characters.', { ignoreCase: true });

	// too many tags
	await page.reload();
	await page.getByRole('button', { name: 'create forum' }).click();
	await page.getByRole('row', { name: 'topic:' }).getByRole('textbox').fill(`Valid Topic ${uniqueId}`);
	await page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor').fill('This is a description.');
	await expect(page.getByRole('row', { name: 'description:' }).locator('div.rich-text-editor')).toContainText('This is a description.', { timeout: 10000 });
	
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
	await expect(page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor')).toContainText('This is a message.', { timeout: 10000 });
	await page.getByRole('button', { name: 'Submit' }).click();
	await expect(page.locator('#lingo-app')).toContainText('Field "title" exceeds max length of 1000 characters.', { ignoreCase: true });

	// long message - rich text tests are not reliable
	// await page.reload();
	// await page.getByRole('button', { name: 'create thread' }).click();
	// await page.getByRole('row', { name: 'title:' }).getByRole('textbox').fill(`Valid Title ${uniqueId}`);
	// await page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor').fill(longRichText);
	// await expect(page.getByRole('row', { name: 'message:' }).locator('div.rich-text-editor')).toContainText(longRichText.slice(0, 20), { timeout: 10000 });
	// await page.getByRole('button', { name: 'Submit' }).click();
	// await expect(page.locator('#lingo-app')).toContainText('Field "message" exceeds max length of 25000 characters.', { ignoreCase: true });

	
	
	//
	// create invalid reply
	//

	// long message - rich text tests are not reliable
	// await page.goto(`${host}/social/forum`);
	// await page.locator('tr').nth(1).click();
	// await expect(page.locator('h1')).toContainText(':: Workflow Forum ::');
	// await page.locator('tr').nth(2).click();
	// await expect(page.locator('#lingo-app')).toContainText(':: thread ::', { ignoreCase: true });

});
