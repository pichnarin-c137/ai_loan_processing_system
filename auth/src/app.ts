import { Hono } from 'hono';

// Caddy (production) and the Vite dev server send /api/auth/* here.
export function createApp(auth: { handler: (request: Request) => Promise<Response> }) {
	const app = new Hono().basePath('/api/auth');
	app.get('/ok', (c) => c.json({ ok: true }));
	app.all('/*', (c) => auth.handler(c.req.raw));
	return app;
}
