import { authClient } from '#lib/auth/client.js';

/** Fetch a new token 60 seconds before the old one expires, so a request never goes out with a stale one. */
const REFRESH_EARLY_MS = 60_000;

export interface TokenCache {
	/** A token that is still valid for at least a minute, or null when nobody is signed in. */
	get(): Promise<string | null>;
	/** Fetch a new token now, for example after the API answered 401. */
	refresh(): Promise<string | null>;
	/** Forget the token. Called on sign-out. */
	clear(): void;
}

/** Reads `exp` (seconds) from a JWT, without checking the signature: the API does that. */
export function tokenExpiry(token: string): number {
	const payload = token.split('.')[1];
	if (!payload) return 0;
	try {
		const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
		const { exp } = JSON.parse(json) as { exp?: unknown };
		return typeof exp === 'number' ? exp * 1000 : 0;
	} catch {
		return 0;
	}
}

/**
 * Keeps the API token in memory only, never in storage or the URL.
 * Callers that ask at the same time share one fetch.
 */
export function createTokenCache(
	fetchToken: () => Promise<string | null>,
	now: () => number = Date.now
): TokenCache {
	let token: string | null = null;
	let expiresAt = 0;
	let pending: Promise<string | null> | null = null;
	// Bumped by clear(), so a fetch that started before sign-out can't store its token afterwards.
	let generation = 0;

	function refresh(): Promise<string | null> {
		if (pending) return pending;
		const started = generation;
		const request = fetchToken()
			.then((fresh) => {
				if (started === generation) {
					token = fresh;
					expiresAt = fresh ? tokenExpiry(fresh) : 0;
				}
				return fresh;
			})
			.finally(() => {
				if (pending === request) pending = null;
			});
		pending = request;
		return request;
	}

	return {
		get() {
			if (token && now() < expiresAt - REFRESH_EARLY_MS) return Promise.resolve(token);
			return refresh();
		},
		refresh,
		clear() {
			generation += 1;
			token = null;
			expiresAt = 0;
			pending = null;
		}
	};
}

export const apiToken = createTokenCache(async () => {
	const { data } = await authClient.token();
	return data?.token ?? null;
});
