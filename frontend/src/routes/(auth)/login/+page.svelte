<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { isRole } from 'auth/roles';
	import { authClient } from '#lib/auth/client.js';
	import { homeFor, safeNext } from '#lib/auth/navigation.js';
	import { m } from '#lib/paraglide/messages.js';

	let email = $state('');
	let password = $state('');
	let error = $state<string | null>(null);
	let busy = $state(false);

	async function signIn(event: SubmitEvent) {
		event.preventDefault();
		busy = true;
		error = null;
		try {
			const { data, error: failure } = await authClient.signIn.email({ email, password });
			const role = data?.user.role;
			if (!isRole(role)) {
				// A role this app doesn't know has no pages to go to, so don't leave it signed in.
				if (data) await authClient.signOut();
				// One message for a wrong email or a wrong password, so the form doesn't reveal which
				// emails have accounts.
				error = failure?.status === 429 ? m.login_rate_limited() : m.login_failed();
				return;
			}
			const next = safeNext(page.url.searchParams.get('next')) ?? homeFor(role);
			// eslint-disable-next-line svelte/no-navigation-without-resolve -- a checked path on this site
			await goto(next, { replaceState: true });
		} catch {
			error = m.network_error();
		} finally {
			busy = false;
		}
	}
</script>

<main class="mx-auto w-full max-w-sm flex-1 px-4 py-10">
	<h1 class="text-xl font-semibold">{m.login_title()}</h1>
	<form onsubmit={signIn} class="mt-6 flex flex-col gap-4">
		<label class="flex flex-col gap-1 text-sm">
			{m.field_email()}
			<input
				type="email"
				autocomplete="username"
				required
				bind:value={email}
				class="rounded border border-slate-300 px-3 py-2"
			/>
		</label>
		<label class="flex flex-col gap-1 text-sm">
			{m.field_password()}
			<input
				type="password"
				autocomplete="current-password"
				required
				bind:value={password}
				class="rounded border border-slate-300 px-3 py-2"
			/>
		</label>
		{#if error}
			<p role="alert" class="text-sm text-red-700">{error}</p>
		{/if}
		<button
			type="submit"
			disabled={busy}
			class="rounded bg-slate-900 px-4 py-2 font-medium text-white disabled:opacity-50"
		>
			{m.login_title()}
		</button>
	</form>
	<p class="mt-6 text-sm text-slate-600">{m.login_no_account()}</p>
</main>
