import { paraglideVitePlugin } from '@inlang/paraglide-js';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vitest/config';
import { playwright } from '@vitest/browser-playwright';
import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';

// In Docker Compose these point at the service names; on the host, at localhost.
const authUrl = process.env.AUTH_URL ?? 'http://localhost:3001';
const apiUrl = process.env.API_URL ?? 'http://localhost:8000';

export default defineConfig({
	// One .env at the repo root serves every service.
	envDir: '..',
	plugins: [
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// SPA: every unknown path falls back to index.html and is routed in the browser.
			adapter: adapter({ fallback: 'index.html' })
		}),
		// Keep these settings in sync with the `prepare` script in package.json, which compiles the
		// messages before the first dev server or typecheck run.
		paraglideVitePlugin({
			project: './project.inlang',
			outdir: './src/lib/paraglide',
			emitTsDeclarations: true,
			strategy: ['localStorage', 'preferredLanguage', 'baseLocale']
		})
	],
	server: {
		// Same paths as production, where Caddy does this routing.
		proxy: {
			// xfwd passes the client IP on in X-Forwarded-For, which Better Auth's rate limits use.
			'/api/auth': { target: authUrl, changeOrigin: true, xfwd: true },
			'/api': { target: apiUrl, changeOrigin: true, ws: true }
		}
	},
	test: {
		expect: { requireAssertions: true },
		projects: [
			{
				extends: './vite.config.ts',
				test: {
					name: 'client',
					browser: {
						enabled: true,
						provider: playwright(),
						instances: [{ browser: 'chromium', headless: true }]
					},
					include: ['src/**/*.svelte.{test,spec}.ts']
				}
			},
			{
				extends: './vite.config.ts',
				test: {
					name: 'server',
					environment: 'node',
					include: ['src/**/*.{test,spec}.ts'],
					exclude: ['src/**/*.svelte.{test,spec}.ts']
				}
			}
		]
	}
});
