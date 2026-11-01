<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { forgetUserData } from '#lib/api/query.js';
	import { authClient, INVITE_HEADER, invites, type InviteCheck } from '#lib/auth/client.js';
	import { homeFor } from '#lib/auth/navigation.js';
	import { roleLabel } from '#lib/auth/role-label.js';
	import { m } from '#lib/paraglide/messages.js';

	// The token is after the #, so it never reaches a server log or a Referer header.
	const token = page.url.hash.slice(1);

	let name = $state('');
	let email = $state('');
	let password = $state('');
	let confirm = $state('');
	let error = $state<string | null>(null);
	let busy = $state(false);

	/** The invite, or the message to show instead of the form. */
	async function checkInvite(): Promise<InviteCheck | string> {
		if (!token) return m.invite_invalid();
		try {
			const { data, error: failure } = await invites.check(token);
			if (failure?.status === 429) return m.login_rate_limited();
			if (failure && failure.status >= 500) return m.network_error();
			if (!data?.valid || !data.role) return m.invite_invalid();
			email = data.email ?? '';
			return data;
		} catch {
			return m.network_error();
		}
	}

	const invite = checkInvite();

	async function signUp(event: SubmitEvent, found: InviteCheck) {
		event.preventDefault();
		if (password !== confirm) {
			error = m.invite_password_mismatch();
			return;
		}
		busy = true;
		error = null;
		try {
			const { error: failure } = await authClient.signUp.email(
				{ name, email, password },
				{ headers: { [INVITE_HEADER]: token } }
			);
			if (failure) {
				error = failure.status === 429 ? m.login_rate_limited() : m.invite_failed();
				return;
			}
		} catch {
			error = m.network_error();
			return;
		} finally {
			busy = false;
		}
		// Signing up also signs in. The role comes from the invite, never from the form.
		// Forget any token or data an earlier session left in this tab.
		forgetUserData();
		// eslint-disable-next-line svelte/no-navigation-without-resolve -- a fixed path from homeFor
		await goto(homeFor(found.role), { replace: true });
	}
</script>

<main class="mx-auto w-full max-w-sm flex-1 px-4 py-10">
	<h1 class="text-xl font-semibold">{m.invite_title()}</h1>
	{#await invite}
		<p class="mt-6 text-slate-600">{m.invite_checking()}</p>
	{:then found}
		{#if typeof found !== 'string' && found.role}
			<p class="mt-2 text-slate-600">{m.invite_as_role({ role: roleLabel(found.role) })}</p>
			<form onsubmit={(event) => signUp(event, found)} class="mt-6 flex flex-col gap-4">
				<label class="flex flex-col gap-1 text-sm">
					{m.field_name()}
					<input
						autocomplete="name"
						required
						bind:value={name}
						class="rounded border border-slate-300 px-3 py-2"
					/>
				</label>
				<label class="flex flex-col gap-1 text-sm">
					{m.field_email()}
					<input
						type="email"
						autocomplete="username"
						required
						readonly={Boolean(found.email)}
						bind:value={email}
						class="rounded border border-slate-300 px-3 py-2 read-only:bg-slate-100"
					/>
				</label>
				<label class="flex flex-col gap-1 text-sm">
					{m.field_password()}
					<input
						type="password"
						autocomplete="new-password"
						minlength="12"
						required
						aria-describedby="password-hint"
						bind:value={password}
						class="rounded border border-slate-300 px-3 py-2"
					/>
					<span id="password-hint" class="text-slate-500">{m.field_password_hint()}</span>
				</label>
				<label class="flex flex-col gap-1 text-sm">
					{m.field_password_confirm()}
					<input
						type="password"
						autocomplete="new-password"
						minlength="12"
						required
						bind:value={confirm}
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
					{m.invite_submit()}
				</button>
			</form>
		{:else}
			<p role="alert" class="mt-6 text-slate-700">
				{typeof found === 'string' ? found : m.invite_invalid()}
			</p>
		{/if}
	{/await}
</main>
