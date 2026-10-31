import { serve } from '@hono/node-server';
import { app } from './app.ts';

const port = Number(process.env.PORT ?? 3001);

const server = serve({ fetch: app.fetch, port, hostname: '0.0.0.0' }, (info) => {
	console.log(`auth listening on :${String(info.port)}`);
});

// Docker sends SIGTERM on stop; close open connections so the container exits promptly.
for (const signal of ['SIGINT', 'SIGTERM'] as const) {
	process.on(signal, () => {
		server.close(() => process.exit(0));
	});
}
