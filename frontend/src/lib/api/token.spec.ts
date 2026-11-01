import { describe, expect, it, vi } from 'vitest';
import { createTokenCache, tokenExpiry } from './token';

/** An unsigned JWT with the given `exp` (seconds). Only the payload matters here. */
function jwt(exp: number): string {
	const payload = btoa(JSON.stringify({ exp, sub: 'u1' }))
		.replace(/\+/g, '-')
		.replace(/\//g, '_')
		.replace(/=+$/, '');
	return `header.${payload}.signature`;
}

describe('tokenExpiry', () => {
	it('reads exp as milliseconds', () => {
		expect(tokenExpiry(jwt(1_800_000_000))).toBe(1_800_000_000_000);
	});

	it('gives 0 for anything that is not a JWT with a numeric exp', () => {
		expect(tokenExpiry('not-a-jwt')).toBe(0);
		expect(tokenExpiry('a.%%%.c')).toBe(0);
		expect(tokenExpiry(`a.${btoa('{"exp":"soon"}')}.c`)).toBe(0);
	});
});

describe('createTokenCache', () => {
	const start = 1_800_000_000_000;

	it('reuses a token until a minute before it expires', async () => {
		let now = start;
		const first = jwt(start / 1000 + 15 * 60);
		const second = jwt(start / 1000 + 30 * 60);
		const fetchToken = vi.fn().mockResolvedValueOnce(first).mockResolvedValueOnce(second);
		const cache = createTokenCache(fetchToken, () => now);

		expect(await cache.get()).toBe(first);
		now = start + 13 * 60_000;
		expect(await cache.get()).toBe(first);
		expect(fetchToken).toHaveBeenCalledTimes(1);

		now = start + 14 * 60_000 + 1;
		expect(await cache.get()).toBe(second);
		expect(fetchToken).toHaveBeenCalledTimes(2);
	});

	it('shares one fetch between callers that ask at the same time', async () => {
		const token = jwt(start / 1000 + 900);
		const fetchToken = vi.fn().mockResolvedValue(token);
		const cache = createTokenCache(fetchToken, () => start);

		const results = await Promise.all([cache.get(), cache.get(), cache.refresh()]);
		expect(results).toEqual([token, token, token]);
		expect(fetchToken).toHaveBeenCalledTimes(1);
	});

	it('forgets the token on clear, even one still being fetched', async () => {
		let release: (token: string) => void = () => undefined;
		const late = jwt(start / 1000 + 900);
		const fresh = jwt(start / 1000 + 1800);
		const fetchToken = vi
			.fn<() => Promise<string | null>>()
			.mockImplementationOnce(() => new Promise((resolve) => (release = resolve)))
			.mockResolvedValueOnce(fresh);
		const cache = createTokenCache(fetchToken, () => start);

		const inFlight = cache.get();
		cache.clear();
		release(late);
		await inFlight;

		// The fetch from before sign-out must not be served afterwards.
		expect(await cache.get()).toBe(fresh);
		expect(fetchToken).toHaveBeenCalledTimes(2);
	});

	it('gives null when nobody is signed in', async () => {
		const cache = createTokenCache(
			() => Promise.resolve(null),
			() => start
		);
		expect(await cache.get()).toBeNull();
	});
});
