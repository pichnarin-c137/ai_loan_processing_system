import { betterAuth } from 'better-auth';
import { APIError, createAuthMiddleware, getSessionFromCtx } from 'better-auth/api';
import { admin } from 'better-auth/plugins/admin';
import { jwt } from 'better-auth/plugins/jwt';
import pg from 'pg';
import * as z from 'zod';
import type { Env } from './env.ts';
import { invite, inviteDatabaseHooks } from './invite-plugin.ts';
import { ac, roles } from './roles.ts';

/** Better Auth's tables live in the `auth` schema, owned by the loan_desk_auth role. */
export function createPool(env: Env): pg.Pool {
	return new pg.Pool({ connectionString: env.databaseUrl, options: '-c search_path=auth' });
}

export function createAuth(env: Env, pool: pg.Pool) {
	return betterAuth({
		appName: env.appName,
		baseURL: env.baseURL,
		basePath: '/api/auth',
		secret: env.secret,
		trustedOrigins: [env.baseURL],
		database: pool,
		// No email service yet, so no verification or reset mail; an admin can set a new password.
		emailAndPassword: { enabled: true, minPasswordLength: 12 },
		// Off by default outside production. The client IP comes from X-Forwarded-For (see README).
		rateLimit: {
			enabled: true,
			customRules: {
				'/sign-in/email': { window: 60, max: 5 },
				'/sign-up/email': { window: 60, max: 5 }
			}
		},
		advanced: { ipAddress: { trustedProxies: env.trustedProxies } },
		databaseHooks: inviteDatabaseHooks(),
		hooks: {
			// Better Auth already stops admins banning themselves. This also stops them changing
			// their own role, so the last admin can't lock everyone out of /admin by mistake.
			before: createAuthMiddleware(async (ctx) => {
				if (ctx.path !== '/admin/set-role') return;
				const target = z.object({ userId: z.string() }).safeParse(ctx.body);
				const session = await getSessionFromCtx(ctx);
				if (target.success && session?.user.id === target.data.userId) {
					throw new APIError('BAD_REQUEST', { message: 'You cannot change your own role' });
				}
			})
		},
		plugins: [
			admin({ ac, roles, defaultRole: 'customer', adminRoles: ['admin'] }),
			// FastAPI checks these tokens against /api/auth/jwks. The payload holds only the
			// role; `sub` is the user id.
			jwt({
				jwt: {
					issuer: env.baseURL,
					audience: env.jwtAudience,
					expirationTime: '15m',
					definePayload: ({ user }) => ({ role: user.role as string })
				}
			}),
			invite({ siteURL: env.baseURL })
		]
	});
}

export type Auth = ReturnType<typeof createAuth>;
