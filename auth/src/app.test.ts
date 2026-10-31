import { describe, expect, it } from 'vitest';
import { createApp } from './app.ts';

const app = createApp({
	handler: () => Promise.resolve(new Response('from auth', { status: 418 }))
});

describe('auth app', () => {
	it('answers the health route', async () => {
		const response = await app.request('/api/auth/ok');

		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ ok: true });
	});

	it('sends other /api/auth paths to Better Auth', async () => {
		const response = await app.request('/api/auth/get-session');

		expect(response.status).toBe(418);
	});

	it('returns 404 outside /api/auth', async () => {
		const response = await app.request('/ok');

		expect(response.status).toBe(404);
	});
});
