import type { Config } from 'prettier';

const config: Config = {
	useTabs: true,
	singleQuote: true,
	trailingComma: 'none',
	printWidth: 100,
	plugins: ['prettier-plugin-svelte', 'prettier-plugin-tailwindcss'],
	overrides: [
		{ files: '*.svelte', options: { parser: 'svelte' } },
		{ files: ['*.yml', '*.yaml', '*.md'], options: { useTabs: false } }
	],
	tailwindStylesheet: './frontend/src/routes/layout.css'
};

export default config;
