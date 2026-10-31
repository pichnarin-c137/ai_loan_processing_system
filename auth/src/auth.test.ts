// Runs Better Auth against a real Postgres database; see src/test/global-setup.ts.
import { createLocalJWKSet, jwtVerify, type JSONWebKeySet } from 'jose';
import { afterAll, beforeAll, describe, expect, inject, it } from 'vitest';
import { createApp } from './app.ts';
import { createAuth, createPool } from './auth.ts';
import { hashToken } from './invite-plugin.ts';
import { INVITE_HEADER } from './invite-shared.ts';
import type { Role } from './roles.ts';
import { AUDIENCE, SITE, testEnv } from './test/env.ts';

const PASSWORD = 'long-enough-password';

const pool = createPool(testEnv(inject('authDatabaseUrl')));
const auth = createAuth(testEnv(inject('authDatabaseUrl')), pool);
const app = createApp(auth);

afterAll(() => pool.end());

let sequence = 0;
const uniqueEmail = (label: string) => `${label}-${String(++sequence)}@example.test`;
// Rate limits count per IP and path, so each request gets its own address unless a test sets one.
const nextIp = () => `10.1.${String((++sequence >> 8) & 255)}.${String(sequence & 255)}`;

type CallOptions = {
	body?: unknown;
	cookie?: string;
	headers?: Record<string, string>;
	ip?: string;
};

async function call(path: string, options: CallOptions = {}): Promise<Response> {
	const headers = new Headers(options.headers);
	headers.set('origin', SITE);
	headers.set('x-forwarded-for', options.ip ?? nextIp());
	if (options.cookie) headers.set('cookie', options.cookie);
	let body: string | undefined;
	if (options.body !== undefined) {
		headers.set('content-type', 'application/json');
		body = JSON.stringify(options.body);
	}
	return app.request(`${SITE}/api/auth${path}`, { method: body ? 'POST' : 'GET', headers, body });
}

function cookieFrom(response: Response): string {
	return response.headers
		.getSetCookie()
		.map((cookie) => cookie.split(';')[0])
		.join('; ');
}

async function signIn(email: string): Promise<string> {
	const response = await call('/sign-in/email', { body: { email, password: PASSWORD } });
	expect(response.status).toBe(200);
	return cookieFrom(response);
}

/** Creates a user the way the seed script does, then signs in. */
async function createUser(role: Role): Promise<{ id: string; email: string; cookie: string }> {
	const email = uniqueEmail(role);
	const { user } = await auth.api.createUser({
		body: { email, password: PASSWORD, name: role, role }
	});
	return { id: user.id, email, cookie: await signIn(email) };
}

async function createInvite(
	adminCookie: string,
	body: { role: Role; email?: string }
): Promise<string> {
	const response = await call('/invite/create', { body, cookie: adminCookie });
	expect(response.status).toBe(200);
	const { url } = (await response.json()) as { url: string };
	expect(url.startsWith(`${SITE}/invite#`)).toBe(true);
	return new URL(url).hash.slice(1);
}

function signUp(token: string | null, email: string, extra: object = {}): Promise<Response> {
	return call('/sign-up/email', {
		body: { name: 'Test User', email, password: PASSWORD, ...extra },
		headers: token ? { [INVITE_HEADER]: token } : {}
	});
}

async function roleOf(email: string): Promise<string | undefined> {
	const { rows } = await pool.query<{ role: string }>('SELECT role FROM "user" WHERE email = $1', [
		email
	]);
	return rows[0]?.role;
}

async function inviteRow(token: string) {
	const { rows } = await pool.query<{ usedAt: Date | null; usedBy: string | null }>(
		'SELECT "usedAt", "usedBy" FROM invite WHERE "tokenHash" = $1',
		[hashToken(token)]
	);
	return rows[0];
}

/** Waits until a query in the test database is blocked on a lock. */
async function waitForLockWait(): Promise<void> {
	for (let attempt = 0; attempt < 100; attempt++) {
		const { rows } = await pool.query<{ count: string }>(
			`SELECT count(*) FROM pg_stat_activity
			 WHERE datname = current_database() AND wait_event_type = 'Lock'`
		);
		if (rows[0]?.count !== '0') return;
		await new Promise((resolve) => setTimeout(resolve, 50));
	}
	throw new Error('Sign-up never waited on the held row');
}

let admin: { id: string; cookie: string };
let customer: { id: string; cookie: string };

beforeAll(async () => {
	admin = await createUser('admin');
	customer = await createUser('customer');
});

describe('invite-only sign-up', () => {
	it('refuses sign-up without a valid invite and creates no user', async () => {
		const email = uniqueEmail('no-invite');
		expect((await signUp(null, email)).status).toBe(400);
		expect((await signUp('not-a-real-token', email)).status).toBe(400);
		expect(await roleOf(email)).toBeUndefined();
	});

	it('gives the new user the invite role and marks the invite used', async () => {
		const token = await createInvite(admin.cookie, { role: 'analyst' });
		const email = uniqueEmail('invited');
		const response = await signUp(token, email);
		expect(response.status).toBe(200);
		const { user } = (await response.json()) as { user: { id: string } };
		expect(await roleOf(email)).toBe('analyst');
		const row = await inviteRow(token);
		expect(row?.usedAt).toBeInstanceOf(Date);
		expect(row?.usedBy).toBe(user.id);
	});

	it('never takes the role from the request body', async () => {
		const token = await createInvite(admin.cookie, { role: 'customer' });
		const email = uniqueEmail('wants-admin');
		expect((await signUp(token, email, { role: 'admin' })).status).toBe(400);
		expect(await roleOf(email)).toBeUndefined();
	});

	it('refuses an invite that was already used', async () => {
		const token = await createInvite(admin.cookie, { role: 'officer' });
		expect((await signUp(token, uniqueEmail('first'))).status).toBe(200);
		const second = uniqueEmail('second');
		expect((await signUp(token, second)).status).toBe(400);
		expect(await roleOf(second)).toBeUndefined();
	});

	it('refuses an expired invite', async () => {
		const token = await createInvite(admin.cookie, { role: 'officer' });
		await pool.query(
			`UPDATE invite SET "expiresAt" = now() - interval '1 minute' WHERE "tokenHash" = $1`,
			[hashToken(token)]
		);
		expect((await signUp(token, uniqueEmail('late'))).status).toBe(400);
		const check = await call('/invite/check', { body: { token } });
		expect(await check.json()).toEqual({ valid: false, role: null, email: null });
	});

	it('keeps an invite for the email it names', async () => {
		const invited = uniqueEmail('named');
		const token = await createInvite(admin.cookie, { role: 'risk', email: invited });
		expect((await signUp(token, uniqueEmail('someone-else'))).status).toBe(400);
		expect((await signUp(token, invited)).status).toBe(200);
		expect(await roleOf(invited)).toBe('risk');
	});

	it('lets only one of two simultaneous sign-ups use an invite', async () => {
		const token = await createInvite(admin.cookie, { role: 'manager' });
		const responses = await Promise.all([
			signUp(token, uniqueEmail('race-a')),
			signUp(token, uniqueEmail('race-b'))
		]);
		expect(responses.map((response) => response.status).sort()).toEqual([200, 400]);
	});

	it('gives the invite back if the account cannot be created', async () => {
		const token = await createInvite(admin.cookie, { role: 'analyst' });
		const email = uniqueEmail('taken');
		// An uncommitted user with the same email: sign-up passes its duplicate check, uses the
		// invite, then waits on the unique email and fails once this transaction commits.
		const holder = await pool.connect();
		try {
			await holder.query('BEGIN');
			await holder.query(
				`INSERT INTO "user" (id, name, email, "emailVerified", "createdAt", "updatedAt")
				 VALUES ($1, 'Holder', $2, false, now(), now())`,
				[`holder-${String(++sequence)}`, email]
			);
			const pending = signUp(token, email);
			await waitForLockWait();
			await holder.query('COMMIT');
			expect((await pending).status).not.toBe(200);
		} finally {
			await holder.query('ROLLBACK');
			holder.release();
		}
		expect((await inviteRow(token))?.usedAt).toBeNull();
		expect((await signUp(token, uniqueEmail('retry'))).status).toBe(200);
	});

	it('tells the invite page whether a token is valid', async () => {
		const invited = uniqueEmail('check');
		const token = await createInvite(admin.cookie, { role: 'committee', email: invited });
		const valid = await call('/invite/check', { body: { token } });
		expect(await valid.json()).toEqual({ valid: true, role: 'committee', email: invited });
		const unknown = await call('/invite/check', { body: { token: 'not-a-real-token' } });
		expect(await unknown.json()).toEqual({ valid: false, role: null, email: null });
	});

	it('stores only the sha256 of the token', async () => {
		const token = await createInvite(admin.cookie, { role: 'customer' });
		const count = async (value: string) => {
			const { rows } = await pool.query<{ count: string }>(
				'SELECT count(*) FROM invite WHERE "tokenHash" = $1',
				[value]
			);
			return rows[0]?.count;
		};
		expect(await count(token)).toBe('0');
		expect(await count(hashToken(token))).toBe('1');
	});
});

describe('invite management', () => {
	it('needs a signed-in admin to create invites', async () => {
		expect((await call('/invite/create', { body: { role: 'admin' } })).status).toBe(401);
		const response = await call('/invite/create', {
			body: { role: 'admin' },
			cookie: customer.cookie
		});
		expect(response.status).toBe(403);
	});

	it('lists invites for admins without their token hashes', async () => {
		await createInvite(admin.cookie, { role: 'officer' });
		const response = await call('/invite/list', { cookie: admin.cookie });
		expect(response.status).toBe(200);
		const invites = (await response.json()) as Record<string, unknown>[];
		expect(invites.length).toBeGreaterThan(0);
		for (const item of invites) expect(item).not.toHaveProperty('tokenHash');
		expect((await call('/invite/list', { cookie: customer.cookie })).status).toBe(403);
	});
});

describe('admin limits', () => {
	it('stops admins from impersonating or deleting users', async () => {
		const target = await createUser('customer');
		const body = { userId: target.id };
		expect((await call('/admin/impersonate-user', { body, cookie: admin.cookie })).status).toBe(
			403
		);
		expect((await call('/admin/remove-user', { body, cookie: admin.cookie })).status).toBe(403);
	});

	it('stops admins from changing their own role', async () => {
		const self = await createUser('admin');
		const other = await createUser('customer');
		const setRole = (userId: string) =>
			call('/admin/set-role', { body: { userId, role: 'officer' }, cookie: self.cookie });
		expect((await setRole(self.id)).status).toBe(400);
		expect(await roleOf(self.email)).toBe('admin');
		expect((await setRole(other.id)).status).toBe(200);
		expect(await roleOf(other.email)).toBe('officer');
	});

	it('refuses users created outside sign-up and the admin API', async () => {
		const { internalAdapter } = await auth.$context;
		const email = uniqueEmail('direct');
		// Even the admin method is refused unless it comes through the admin endpoint.
		const created = internalAdapter.createUser({ email, name: 'Direct' }, { method: 'admin' });
		await expect(created).rejects.toThrow('Accounts are created by invite only');
		expect(await roleOf(email)).toBeUndefined();
	});

	it('rate-limits repeated sign-in attempts from one address', async () => {
		const ip = '10.99.0.1';
		const attempt = () =>
			call('/sign-in/email', {
				body: { email: 'nobody@example.test', password: 'wrong-password' },
				ip
			});
		for (let i = 0; i < 5; i++) expect((await attempt()).status).toBe(401);
		expect((await attempt()).status).toBe(429);
	});
});

describe('JWT for the API', () => {
	it('issues a token that verifies against the JWKS', async () => {
		const analyst = await createUser('analyst');
		const tokenResponse = await call('/token', { cookie: analyst.cookie });
		expect(tokenResponse.status).toBe(200);
		const { token } = (await tokenResponse.json()) as { token: string };
		const jwks = (await (await call('/jwks')).json()) as JSONWebKeySet;
		const { payload, protectedHeader } = await jwtVerify(token, createLocalJWKSet(jwks), {
			issuer: SITE,
			audience: AUDIENCE,
			algorithms: ['EdDSA']
		});
		expect(protectedHeader.alg).toBe('EdDSA');
		expect(payload.sub).toBe(analyst.id);
		expect(payload.role).toBe('analyst');
		// Nothing else about the user goes into the token.
		expect(Object.keys(payload).sort()).toEqual(['aud', 'exp', 'iat', 'iss', 'role', 'sub']);
	});
});
