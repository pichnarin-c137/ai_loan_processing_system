import { Hono } from 'hono';

// Caddy (production) and the Vite dev server send /api/auth/* here.
// Better Auth is mounted on this app in Step 4.
export const app = new Hono().basePath('/api/auth');

app.get('/ok', (c) => c.json({ ok: true }));
