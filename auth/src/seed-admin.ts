// Creates the first admin account. Safe to run again: it does nothing if the email exists.
// docker compose -f infra/compose.yml run --rm -e ADMIN_EMAIL -e ADMIN_PASSWORD -e ADMIN_NAME auth node src/seed-admin.ts
import { createAuth, createPool } from './auth.ts';
import { loadEnv } from './env.ts';

const email = process.env.ADMIN_EMAIL?.trim().toLowerCase();
const password = process.env.ADMIN_PASSWORD;
const name = process.env.ADMIN_NAME?.trim() || 'Admin';

if (!email || !password) {
	console.error('Set ADMIN_EMAIL and ADMIN_PASSWORD.');
	process.exit(1);
}
if (password.length < 12) {
	console.error('ADMIN_PASSWORD needs at least 12 characters.');
	process.exit(1);
}

const env = loadEnv();
const pool = createPool(env);
try {
	const auth = createAuth(env, pool);
	const { internalAdapter } = await auth.$context;
	if (await internalAdapter.findUserByEmail(email)) {
		console.log(`An account for ${email} already exists; nothing to do.`);
	} else {
		// Called on the server with no request, so the admin plugin skips its session check.
		await auth.api.createUser({ body: { email, password, name, role: 'admin' } });
		console.log(`Created admin ${email}.`);
	}
} finally {
	await pool.end();
}
