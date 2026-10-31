import { describe, expect, it } from 'vitest';
import { loadEnv, LOCAL_SECRET } from './env.ts';

const STRONG_SECRET = 'a-production-secret-of-at-least-32-chars';

describe('loadEnv', () => {
	it('defaults to the local stack outside production', () => {
		const env = loadEnv({});
		expect(env.databaseUrl).toContain('@localhost:5433/');
		expect(env.baseURL).toBe('http://localhost:5173');
		expect(env.secret).toBe(LOCAL_SECRET);
		expect(env.trustedProxies).toEqual([]);
	});

	it('treats an empty secret as unset', () => {
		expect(loadEnv({ BETTER_AUTH_SECRET: '' }).secret).toBe(LOCAL_SECRET);
		const production = {
			NODE_ENV: 'production',
			AUTH_DATABASE_URL: 'postgres://auth:pw@db:5432/loan_desk',
			BETTER_AUTH_URL: 'https://loans.example.test'
		};
		expect(() => loadEnv({ ...production, BETTER_AUTH_SECRET: '' })).toThrow('BETTER_AUTH_SECRET');
		expect(loadEnv({ ...production, BETTER_AUTH_SECRET: STRONG_SECRET }).secret).toBe(
			STRONG_SECRET
		);
	});

	it('needs the database and site set in production', () => {
		expect(() => loadEnv({ NODE_ENV: 'production', BETTER_AUTH_SECRET: STRONG_SECRET })).toThrow(
			'AUTH_DATABASE_URL'
		);
	});

	it('reads trusted proxies as a comma-separated list', () => {
		const env = loadEnv({ AUTH_TRUSTED_PROXIES: '10.0.0.1, 172.16.0.0/12,' });
		expect(env.trustedProxies).toEqual(['10.0.0.1', '172.16.0.0/12']);
	});
});
