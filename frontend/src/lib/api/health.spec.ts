import { describe, expect, it } from 'vitest';
import { fetchHealth, toServiceStatuses, type HealthReport } from './health';

const healthy: HealthReport = {
	status: 'ok',
	checks: { database: true, redis: true, storage: true }
};

describe('toServiceStatuses', () => {
	it('lists every service in display order', () => {
		expect(toServiceStatuses(healthy, true)).toEqual([
			{ name: 'api', ok: true },
			{ name: 'database', ok: true },
			{ name: 'redis', ok: true },
			{ name: 'storage', ok: true },
			{ name: 'auth', ok: true }
		]);
	});

	it('marks the backend services down when the API did not answer', () => {
		const statuses = toServiceStatuses(null, true);
		expect(statuses.filter((s) => s.ok).map((s) => s.name)).toEqual(['auth']);
	});
});

describe('fetchHealth', () => {
	it('reads a degraded report from a 503 response', async () => {
		const degraded: HealthReport = {
			...healthy,
			status: 'degraded',
			checks: { ...healthy.checks, redis: false }
		};
		const fetchFn: typeof fetch = (input) =>
			Promise.resolve(
				input === '/api/health'
					? Response.json(degraded, { status: 503 })
					: Response.json({ ok: true })
			);

		const statuses = await fetchHealth(fetchFn);

		expect(statuses.find((s) => s.name === 'api')?.ok).toBe(true);
		expect(statuses.find((s) => s.name === 'redis')?.ok).toBe(false);
		expect(statuses.find((s) => s.name === 'auth')?.ok).toBe(true);
	});

	it('reports everything down when no request succeeds', async () => {
		const fetchFn: typeof fetch = () => Promise.reject(new TypeError('network error'));

		const statuses = await fetchHealth(fetchFn);

		expect(statuses.every((s) => !s.ok)).toBe(true);
	});
});
