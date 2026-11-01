import js from '@eslint/js';
import prettier from 'eslint-config-prettier';
import svelte from 'eslint-plugin-svelte';
import { defineConfig, globalIgnores } from 'eslint/config';
import globals from 'globals';
import ts from 'typescript-eslint';

export default defineConfig(
	globalIgnores([
		'**/node_modules/',
		'**/.svelte-kit/',
		'**/build/',
		'**/dist/',
		'**/test-results/',
		'**/playwright-report/',
		'frontend/src/lib/paraglide/',
		'frontend/src/lib/api/schema.d.ts',
		'backend/',
		'datagen/',
		'eval/'
	]),
	js.configs.recommended,
	ts.configs.strictTypeChecked,
	svelte.configs.recommended,
	prettier,
	svelte.configs.prettier,
	{
		languageOptions: {
			parserOptions: {
				projectService: true,
				tsconfigRootDir: import.meta.dirname,
				extraFileExtensions: ['.svelte']
			}
		},
		rules: {
			// TypeScript already checks for undefined names.
			'no-undef': 'off'
		}
	},
	{
		files: ['frontend/src/**'],
		languageOptions: { globals: globals.browser },
		rules: {
			// The app runs in the browser. TypeScript can't catch these, because Vite's types pull in
			// the Node globals for the whole frontend project.
			'no-restricted-globals': [
				'error',
				...['process', 'Buffer', 'global', '__dirname', '__filename', 'require'].map((name) => ({
					name,
					message: 'Node-only global; use import.meta.env or a browser API.'
				}))
			]
		}
	},
	{
		files: ['auth/**', 'frontend/e2e/**', '**/*.config.ts'],
		languageOptions: { globals: globals.node }
	},
	{
		files: ['**/*.svelte', '**/*.svelte.ts'],
		languageOptions: { parserOptions: { parser: ts.parser } },
		rules: {
			// Every component must be TypeScript: <script lang="ts">.
			'svelte/block-lang': ['error', { script: 'ts', style: null }]
		}
	},
	{
		// shadcn-svelte components are copied from its registry. Keep them close to upstream so
		// updates stay easy, and relax the few rules its code doesn't follow.
		files: ['frontend/src/lib/components/ui/**'],
		rules: {
			'@typescript-eslint/no-useless-default-assignment': 'off',
			'@typescript-eslint/no-unsafe-assignment': 'off',
			'svelte/no-navigation-without-resolve': 'off'
		}
	},
	{
		// Config files sit outside the app tsconfigs, so lint them without type information.
		files: ['*.config.ts', '*/*.config.ts'],
		extends: [ts.configs.disableTypeChecked]
	}
);
