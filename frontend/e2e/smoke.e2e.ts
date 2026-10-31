import { expect, test } from '@playwright/test';

// These tests mock the API, so they run against the built SPA alone.
test.beforeEach(async ({ page }) => {
	await page.route('/api/health', (route) =>
		route.fulfill({
			json: { status: 'ok', checks: { database: true, redis: true, storage: true } }
		})
	);
	await page.route('/api/auth/ok', (route) => route.fulfill({ json: { ok: true } }));
});

test('home page shows the sample-data banner and service status', async ({ page }) => {
	await page.goto('/');

	await expect(page.getByRole('note')).toContainText('Sample data only');
	await expect(page.getByRole('status')).toHaveText('All services are running');
});

test('customer and staff pages use their own layouts', async ({ page }) => {
	await page.goto('/my');
	await expect(page.getByRole('navigation', { name: 'Customer menu' })).toBeVisible();

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
