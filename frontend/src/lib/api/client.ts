import createClient from 'openapi-fetch';
import type { paths } from './schema.js';
import { apiToken, type TokenCache } from './token.js';

function withToken(request: Request, token: string | null): Request {
	const headers = new Headers(request.headers);
	if (token) headers.set('Authorization', `Bearer ${token}`);
	return new Request(request, { headers });
}

/** Sends the request with the API token. On a 401 it fetches a new token and tries once more. */
export function createAuthedFetch(tokens: TokenCache, send: typeof fetch = fetch) {
	return async (request: Request): Promise<Response> => {
		// A request body can only be read once, so keep a copy for the retry.
		const spare = request.clone();
		const response = await send(withToken(request, await tokens.get()));
		if (response.status !== 401) return response;
		const token = await tokens.refresh();
		if (!token) return response;
		return send(withToken(spare, token));
	};
}

export const authedFetch = createAuthedFetch(apiToken, (input, init) => fetch(input, init));

/** Typed client for the FastAPI routes. The types come from `pnpm gen:api`. */
export const api = createClient<paths>({ fetch: authedFetch });
