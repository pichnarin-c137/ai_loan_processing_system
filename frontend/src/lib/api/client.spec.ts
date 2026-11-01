import { describe, expect, it, vi } from 'vitest';
import { createAuthedFetch } from './client';
import type { TokenCache } from './token';

/** A token cache, plus its refresh mock so tests can count the calls. */
function tokens(current: string | null, next: string | null) {
	const refresh = vi.fn(() => Promise.resolve(next));
	const cache: TokenCache = { get: () => Promise.resolve(current), refresh, clear: vi.fn() };
	return { cache, refresh };
}

const auth = (request: Request) => request.headers.get('Authorization');

describe('createAuthedFetch', () => {
	it('adds the bearer token', async () => {
		const send = vi.fn((request: Request) =>
			Promise.resolve(new Response(String(auth(request)), { status: 200 }))
		);
		const response = await createAuthedFetch(
			tokens('t1', 't2').cache,
			send as typeof fetch
		)(new Request('http://test/api/me'));
		expect(await response.text()).toBe('Bearer t1');
		expect(send).toHaveBeenCalledTimes(1);
	});

	it('refreshes the token and retries once, body included, after a 401', async () => {
		const seen: { auth: string | null; body: string }[] = [];
		const send = vi.fn(async (request: Request) => {
			seen.push({ auth: auth(request), body: await request.text() });
			return new Response(null, { status: seen.length === 1 ? 401 : 200 });
		});
		const { cache, refresh } = tokens('old', 'new');
		const response = await createAuthedFetch(
			cache,
			send as typeof fetch
		)(new Request('http://test/api/x', { method: 'PUT', body: 'file-bytes' }));
		expect(response.status).toBe(200);
		expect(seen).toEqual([
			{ auth: 'Bearer old', body: 'file-bytes' },
			{ auth: 'Bearer new', body: 'file-bytes' }
		]);
		expect(refresh).toHaveBeenCalledTimes(1);
	});

	it('returns the 401 when no new token can be had', async () => {
		const send = vi.fn(() => Promise.resolve(new Response(null, { status: 401 })));
		const response = await createAuthedFetch(
			tokens('old', null).cache,
			send
		)(new Request('http://test/api/me'));
		expect(response.status).toBe(401);
		expect(send).toHaveBeenCalledTimes(1);
	});

	it('does not retry other errors', async () => {
		const send = vi.fn(() => Promise.resolve(new Response(null, { status: 403 })));
		const { cache, refresh } = tokens('t1', 't2');
		const response = await createAuthedFetch(cache, send)(new Request('http://test/api/me'));
		expect(response.status).toBe(403);
		expect(refresh).not.toHaveBeenCalled();
	});
});
