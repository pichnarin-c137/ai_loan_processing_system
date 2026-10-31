<script lang="ts">
	import { resolve } from '$app/paths';
	import favicon from '#lib/assets/favicon.svg';
	import { appName } from '#lib/config.js';
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale, locales, setLocale } from '#lib/paraglide/runtime.js';
	import './layout.css';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	const currentLocale = getLocale();
	document.documentElement.lang = currentLocale;
</script>

<svelte:head>
	<title>{appName}</title>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="flex min-h-dvh flex-col bg-slate-50 text-slate-900">
	<p
		role="note"
		class="bg-amber-300 px-4 py-1 text-center text-xs font-semibold text-amber-950 uppercase"
	>
		{m.sample_banner()}
	</p>
	<header class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
		<a href={resolve('/')} class="font-semibold">{appName}</a>
		<div role="group" aria-label={m.language_label()} class="flex gap-1 text-sm">
			{#each locales as locale (locale)}
				<button
					type="button"
					aria-pressed={locale === currentLocale}
					onclick={() => setLocale(locale)}
					class="rounded px-2 py-1 aria-pressed:bg-slate-900 aria-pressed:text-white"
				>
					{locale.toUpperCase()}
				</button>
			{/each}
		</div>
	</header>
	<div class="flex flex-1 flex-col">
		{@render children()}
	</div>
</div>
