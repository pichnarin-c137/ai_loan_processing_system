// Creates or updates Better Auth's tables in the auth schema. Compose runs this once before
// the auth service starts; it refuses changes that could lose data.
import { getMigrations } from 'better-auth/db/migration';
import { createAuth, createPool } from './auth.ts';
import { loadEnv } from './env.ts';

const env = loadEnv();
const pool = createPool(env);
try {
	const { toBeCreated, toBeAdded, runMigrations } = await getMigrations(
		createAuth(env, pool).options
	);
	await runMigrations();
	console.log(
		`auth migrations done: ${String(toBeCreated.length)} tables created, ${String(toBeAdded.length)} tables changed`
	);
} finally {
	await pool.end();
}
