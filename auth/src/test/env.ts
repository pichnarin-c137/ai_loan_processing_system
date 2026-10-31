import type { Env } from '../env.ts';

export const SITE = 'http://localhost:5173';
export const AUDIENCE = 'loan-desk-api';

export function testEnv(databaseUrl: string): Env {
	return {
		databaseUrl,
		baseURL: SITE,
		secret: 'test-only-secret-with-at-least-32-characters',
		jwtAudience: AUDIENCE,
		appName: 'Loan Desk',
		trustedProxies: []
	};
}
