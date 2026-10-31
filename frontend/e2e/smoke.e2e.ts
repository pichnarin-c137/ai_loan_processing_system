import { expect, test, type Page } from '@playwright/test';
import type { Role } from 'auth/roles';

/** Fakes a signed-in user. Playwright uses the newest matching route, so calling it again switches role. */
function signInAs(page: Page, role: Role) {
	const now = new Date().toISOString();
	const expiresAt = new Date(Date.now() + 3_600_000).toISOString();
	return page.route('/api/auth/get-session*', (route) =>
		route.fulfill({
			json: {
				session: { id: 's1', userId: 'u1', token: 't1', expiresAt, createdAt: now, updatedAt: now },
				user: {
					id: 'u1',
					name: 'Sample User',
					email: 'sample@example.com',
					emailVerified: false,
					role,
					createdAt: now,
					updatedAt: now
				}
			}
		})
	);
}

// These tests mock the API, so they run against the built SPA alone.
test.beforeEach(async ({ page }) => {
	await page.route('/api/health', (route) =>
		route.fulfill({
			json: { status: 'ok', checks: { database: true, redis: true, storage: true } }
		})
	);
	await page.route('/api/auth/ok', (route) => route.fulfill({ json: { ok: true } }));
	await signInAs(page, 'customer');
});

test('home page shows the sample-data banner and service status', async ({ page }) => {
	await page.goto('/');

	await expect(page.getByRole('note')).toContainText('Sample data only');
	await expect(page.getByRole('status')).toHaveText('All services are running');
});

test('customer and staff pages use their own layouts', async ({ page }) => {
	await page.goto('/my');
	await expect(page.getByRole('navigation', { name: 'Customer menu' })).toBeVisible();

	await signInAs(page, 'officer');
	await page.goto('/staff/queue');
	await expect(page.getByRole('navigation', { name: 'Staff portal' })).toBeVisible();
	await expect(page.getByRole('link', { name: 'Work queue' })).toHaveAttribute(
		'aria-current',
		'page'
	);
});

test('switching to Khmer translates the page and is remembered', async ({ page }) => {
	await page.goto('/my');
	await page.getByRole('button', { name: 'KM' }).click();

	await expect(page.locator('html')).toHaveAttribute('lang', 'km');
	await page.reload();
	await expect(page.getByRole('heading', { level: 1 })).toHaveText('ពាក្យស្នើសុំរបស់ខ្ញុំ');
});

test('signed-out visitors are sent to the login page', async ({ page }) => {
	await page.route('/api/auth/get-session*', (route) => route.fulfill({ json: null }));
	await page.goto('/my');

	await expect(page).toHaveURL('/login?next=%2Fmy');
});

test('admins can read what changed in each release', async ({ page }) => {
	await signInAs(page, 'admin');
	await page.goto('/admin/whats-new');

	await expect(page.getByRole('heading', { level: 1 })).toHaveText("What's new");
	await expect(page.getByRole('link', { name: "What's new" })).toHaveAttribute(
		'aria-current',
		'page'
	);
	await expect(page.getByRole('link', { name: 'PR #1', exact: true })).toBeVisible();
});
