import { readFile } from 'node:fs/promises';
import { getMigrations } from 'better-auth/db/migration';
import pg from 'pg';
import type { TestProject } from 'vitest/node';
import { createAuth, createPool } from '../auth.ts';
import { testEnv } from './env.ts';

declare module 'vitest' {
	export interface ProvidedContext {
		authDatabaseUrl: string;
	}
}

const ROLE_SQL = new URL('../../../infra/postgres/init/02-auth-role.sql', import.meta.url);
const TEST_DB = 'loan_desk_auth_test';
const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]']);
// The owner role from infra/compose.yml; it creates the test database and the auth role.
const ADMIN_URL = new URL(
	process.env.AUTH_TEST_ADMIN_URL ?? 'postgres://loan_desk:loan_desk@localhost:5433/loan_desk'
);

function withDatabase(url: URL, database: string): URL {
	const copy = new URL(url);
	copy.pathname = `/${database}`;
	return copy;
}

async function runAsAdmin(database: string, ...statements: string[]): Promise<void> {
	const client = new pg.Client({
		connectionString: withDatabase(ADMIN_URL, database).href,
		connectionTimeoutMillis: 3000
	});
	await client.connect();
	try {
		for (const statement of statements) await client.query(statement);
	} finally {
		await client.end();
	}
}

/** Creates a fresh database with the auth role, schema and tables, and drops it afterwards. */
export default async function setup(project: TestProject): Promise<() => Promise<void>> {
	// This drops and recreates a database, so never point it at anything but a local Postgres.
	if (!LOCAL_HOSTS.has(ADMIN_URL.hostname)) {
		throw new Error(
			`Auth tests only run against a local Postgres, not ${ADMIN_URL.hostname}. Check AUTH_TEST_ADMIN_URL.`
		);
	}
	const adminDatabase = ADMIN_URL.pathname.slice(1);
	const dropTestDatabase = `DROP DATABASE IF EXISTS ${TEST_DB} WITH (FORCE)`;
	try {
		await runAsAdmin(adminDatabase, dropTestDatabase, `CREATE DATABASE ${TEST_DB}`);
	} catch (error) {
		const shown = new URL(ADMIN_URL);
		shown.password = '***';
		throw new Error(
			`Auth tests need Postgres at ${shown.href}. Start it: docker compose -f infra/compose.yml up -d postgres`,
			{ cause: error }
		);
	}
	await runAsAdmin(TEST_DB, await readFile(ROLE_SQL, 'utf8'));

	const databaseUrl = withDatabase(ADMIN_URL, TEST_DB);
	databaseUrl.username = 'loan_desk_auth';
	databaseUrl.password = 'loan_desk_auth';
	const env = testEnv(databaseUrl.href);
	const pool = createPool(env);
	try {
		const { runMigrations } = await getMigrations(createAuth(env, pool).options);
		await runMigrations();
	} finally {
		await pool.end();
	}
	project.provide('authDatabaseUrl', databaseUrl.href);

	return () => runAsAdmin(adminDatabase, dropTestDatabase);
}
