<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { forgetUserData, queryClient } from '#lib/api/query.js';
	import favicon from '#lib/assets/favicon.svg';
	import { authClient } from '#lib/auth/client.js';
	import { appName } from '#lib/config.js';
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale, locales, setLocale } from '#lib/paraglide/runtime.js';
	import { QueryClientProvider } from '@tanstack/svelte-query';
	import './layout.css';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	const currentLocale = getLocale();
	document.documentElement.lang = currentLocale;

	const session = authClient.useSession();
	const loginPath = resolve('/(auth)/login');

	// A session can also end, or change to someone else, without the Sign out button: it expires,
	// or another tab signs in. Forget the last person's token and data when that happens.
	// (Signing in from signed out is handled by the login and invite pages.)
	let lastUserId: string | null = null;
	$effect(() => {
		if ($session.isPending) return;
		const userId = $session.data?.user.id ?? null;
		if (lastUserId && userId !== lastUserId) forgetUserData();
		lastUserId = userId;
	});

	async function signOut() {
		try {
			await authClient.signOut();
		} finally {
			// Even if the network failed, this tab must not keep the token or the data.
			forgetUserData();
		}
		await goto(loginPath);
	}
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
		<div class="flex items-center gap-4 text-sm">
			{#if $session.data}
				<span class="hidden sm:inline">{$session.data.user.name}</span>
				<button type="button" onclick={signOut} class="rounded border border-slate-300 px-3 py-1">
					{m.nav_sign_out()}
				</button>
			{:else if !$session.isPending && page.url.pathname !== loginPath}
				<a href={loginPath} class="rounded border border-slate-300 px-3 py-1">{m.nav_sign_in()}</a>
			{/if}
			<div role="group" aria-label={m.language_label()} class="flex gap-1">
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
		</div>
	</header>
	<div class="flex flex-1 flex-col">
		<QueryClientProvider client={queryClient}>
			{@render children()}
		</QueryClientProvider>
	</div>
</div>
