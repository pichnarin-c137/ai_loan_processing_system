import { describe, expect, it } from 'vitest';
import { app } from './app.ts';

describe('auth app', () => {
	it('answers the health route', async () => {
		const response = await app.request('/api/auth/ok');

		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('returns 404 outside /api/auth', async () => {
		const response = await app.request('/ok');

		expect(response.status).toBe(404);
	});
});
