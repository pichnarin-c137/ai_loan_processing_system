import { QueryClient } from '@tanstack/svelte-query';
import { ApiError } from './errors.js';
import { apiToken } from './token.js';

export const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			// A 4xx answer won't change on a retry; network errors and 5xx might.
			retry: (failures, error) => failures < 2 && !(error instanceof ApiError && error.status < 500)
		}
	}
});

/**
 * Forgets the API token and every answer loaded with it. Called whenever the signed-in person
 * changes, so nobody sends requests with the last person's token or sees their data.
 */
export function forgetUserData(): void {
	apiToken.clear();
	queryClient.clear();
}
