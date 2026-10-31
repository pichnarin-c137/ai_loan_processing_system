import { describe, expect, it, vi } from 'vitest';
import { page } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import HealthCard from './HealthCard.svelte';

describe('HealthCard', () => {
	it('shows a status for each service', async () => {
		render(HealthCard, {
			services: [
				{ name: 'database', ok: true },
				{ name: 'redis', ok: false }
			],
			onretry: vi.fn()
		});

		await expect.element(page.getByText('Database')).toBeVisible();
		await expect.element(page.getByText('Down', { exact: true })).toBeVisible();
		await expect.element(page.getByRole('status')).toHaveTextContent('Some services are down');
	});

	it('shows a loading state and disables the button while checking', async () => {
		render(HealthCard, { services: undefined, onretry: vi.fn() });

		await expect.element(page.getByRole('status')).toHaveTextContent('Checking…');
		await expect.element(page.getByRole('button', { name: 'Check again' })).toBeDisabled();
	});

	it('calls onretry when asked to check again', async () => {
		const onretry = vi.fn();
		render(HealthCard, { services: [{ name: 'api', ok: true }], onretry });

		await page.getByRole('button', { name: 'Check again' }).click();

		expect(onretry).toHaveBeenCalledOnce();
	});
});
