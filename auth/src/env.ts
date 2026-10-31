import * as z from 'zod';

// Used outside production when BETTER_AUTH_SECRET is unset. Production must set its own secret.
export const LOCAL_SECRET = 'local-only-secret-do-not-use-in-production';

// Outside production, the database and site default to the local stack (as in the backend), so
// `pnpm --filter auth dev`, migrate and seed-admin work on the host. Compose sets its own values.
const LOCAL_DEFAULTS = {
	AUTH_DATABASE_URL: 'postgres://loan_desk_auth:loan_desk_auth@localhost:5433/loan_desk',
	BETTER_AUTH_URL: 'http://localhost:5173'
};

const schema = z
	.object({
		NODE_ENV: z.string().default('development'),
		AUTH_DATABASE_URL: z.url({ protocol: /^postgres(ql)?$/ }),
		BETTER_AUTH_URL: z.url({ protocol: /^https?$/ }),
		BETTER_AUTH_SECRET: z.string().default(LOCAL_SECRET),
		AUTH_JWT_AUDIENCE: z.string().min(1).default('loan-desk-api'),
		APP_NAME: z.string().min(1).default('Loan Desk'),
		// Comma-separated IPs or CIDRs of proxies that append to X-Forwarded-For (see README).
		AUTH_TRUSTED_PROXIES: z.string().default('')
	})
	.superRefine((env, ctx) => {
		if (env.NODE_ENV !== 'production') return;
		if (env.BETTER_AUTH_SECRET === LOCAL_SECRET || env.BETTER_AUTH_SECRET.length < 32) {
			ctx.addIssue({
				code: 'custom',
				path: ['BETTER_AUTH_SECRET'],
				message: 'Set a random secret of at least 32 characters (openssl rand -base64 32)'
			});
		}
	});

export type Env = {
	databaseUrl: string;
	/** The site's public origin, e.g. http://localhost:5173. Also the JWT issuer. */
	baseURL: string;
	secret: string;
	jwtAudience: string;
	appName: string;
	trustedProxies: string[];
};

export function loadEnv(source: NodeJS.ProcessEnv = process.env): Env {
	// Empty values (e.g. `BETTER_AUTH_SECRET=` left in .env) count as unset.
	const set = Object.fromEntries(Object.entries(source).filter(([, value]) => value));
	const result = schema.safeParse(
		set.NODE_ENV === 'production' ? set : { ...LOCAL_DEFAULTS, ...set }
	);
	if (!result.success) {
		// Only the variable names and rules are printed, never the values.
		throw new Error(`Invalid auth environment:\n${z.prettifyError(result.error)}`);
	}
	const env = result.data;
	return {
		databaseUrl: env.AUTH_DATABASE_URL,
		baseURL: new URL(env.BETTER_AUTH_URL).origin,
		secret: env.BETTER_AUTH_SECRET,
		jwtAudience: env.AUTH_JWT_AUDIENCE,
		appName: env.APP_NAME,
		trustedProxies: env.AUTH_TRUSTED_PROXIES.split(',')
			.map((proxy) => proxy.trim())
			.filter(Boolean)
	};
}
