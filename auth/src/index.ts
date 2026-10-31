import { serve } from '@hono/node-server';
import { createApp } from './app.ts';
import { createAuth, createPool } from './auth.ts';
import { loadEnv } from './env.ts';

const env = loadEnv();
const pool = createPool(env);
const app = createApp(createAuth(env, pool));
const port = Number(process.env.PORT ?? 3001);

const server = serve({ fetch: app.fetch, port, hostname: '0.0.0.0' }, (info) => {
	console.log(`auth listening on :${String(info.port)}`);
});

// Docker sends SIGTERM on stop; close open connections so the container exits promptly.
for (const signal of ['SIGINT', 'SIGTERM'] as const) {
	process.on(signal, () => {
		server.close(() => {
			void pool.end().finally(() => process.exit(0));
		});
	});
}
