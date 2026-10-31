<script lang="ts">
	import { ROLES, isRole, type Role } from 'auth/roles';
	import { authClient, invites, type Invite } from '#lib/auth/client.js';
	import { roleLabel } from '#lib/auth/role-label.js';
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale } from '#lib/paraglide/runtime.js';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	interface UserRow {
		id: string;
		name: string;
		email: string;
		role: Role | null;
		banned: boolean;
	}

	let users = $state<UserRow[]>([]);
	let inviteList = $state<Invite[]>([]);
	let error = $state<string | null>(null);

	let inviteRole = $state<Role>('customer');
	let inviteEmail = $state('');
	let inviteDays = $state(7);
	let inviteUrl = $state<string | null>(null);
	let copied = $state(false);
	let busy = $state(false);

	const formatDate = (value: string | Date) =>
		new Date(value).toLocaleString(getLocale(), { dateStyle: 'medium', timeStyle: 'short' });

	function inviteStatus(invite: Invite): string {
		if (invite.usedAt) return m.admin_status_used();
		if (new Date(invite.expiresAt) <= new Date()) return m.admin_status_expired();
		return m.admin_status_pending();
	}

	async function loadUsers() {
		const result = await authClient.admin.listUsers({
			query: { limit: 200, sortBy: 'createdAt', sortDirection: 'desc' }
		});
		if (result.error) {
			error = m.admin_error();
			return;
		}
		users = result.data.users.map((user) => ({
			id: user.id,
			name: user.name,
			email: user.email,
			role: isRole(user.role) ? user.role : null,
			banned: Boolean(user.banned)
		}));
	}

	async function loadInvites() {
		const result = await invites.list();
		if (result.error) error = m.admin_error();
		else inviteList = result.data;
	}

	/** Runs an admin action, then reloads the lists so they show what the server now has. */
	async function run(action: () => Promise<{ error: unknown }>): Promise<boolean> {
		busy = true;
		error = null;
		try {
			const { error: failure } = await action();
			if (failure) error = m.admin_error();
			await Promise.all([loadUsers(), loadInvites()]);
			return !failure;
		} catch {
			error = m.network_error();
			return false;
		} finally {
			busy = false;
		}
	}

	async function createInvite(event: SubmitEvent) {
		event.preventDefault();
		inviteUrl = null;
		copied = false;
		await run(async () => {
			const email = inviteEmail.trim();
			const result = await invites.create({
				role: inviteRole,
				expiresInDays: inviteDays,
				...(email ? { email } : {})
			});
			if (result.data) {
				inviteUrl = result.data.url;
				inviteEmail = '';
			}
			return result;
		});
	}

	async function copyInvite() {
		if (!inviteUrl) return;
		await navigator.clipboard.writeText(inviteUrl);
		copied = true;
	}

	async function setRole(user: UserRow, select: HTMLSelectElement) {
		const role = select.value;
		if (!isRole(role) || role === user.role) return;
		const saved = await run(() => authClient.admin.setRole({ userId: user.id, role }));
		// Otherwise the select keeps showing the role that wasn't saved.
		if (!saved) select.value = user.role ?? '';
	}

	function ban(user: UserRow) {
		if (!confirm(m.admin_ban_confirm({ name: user.name }))) return;
		return run(() => authClient.admin.banUser({ userId: user.id }));
	}

	function unban(user: UserRow) {
		return run(() => authClient.admin.unbanUser({ userId: user.id }));
	}

	void loadUsers();
	void loadInvites();
</script>

<h1 class="text-xl font-semibold">{m.admin_users_title()}</h1>
{#if error}
	<p role="alert" class="mt-4 rounded bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>
{/if}

<section aria-labelledby="invite-heading" class="mt-6 max-w-xl rounded-lg bg-white p-4 shadow-sm">
	<h2 id="invite-heading" class="font-semibold">{m.admin_invite_title()}</h2>
	<form onsubmit={createInvite} class="mt-4 grid gap-4 sm:grid-cols-3">
		<label class="flex flex-col gap-1 text-sm">
			{m.field_role()}
			<select bind:value={inviteRole} class="rounded border border-slate-300 px-2 py-2">
				{#each ROLES as role (role)}
					<option value={role}>{roleLabel(role)}</option>
				{/each}
			</select>
		</label>
		<label class="flex flex-col gap-1 text-sm sm:col-span-2">
			{m.admin_invite_email()}
			<input
				type="email"
				bind:value={inviteEmail}
				aria-describedby="invite-email-hint"
				class="rounded border border-slate-300 px-3 py-2"
			/>
			<span id="invite-email-hint" class="text-slate-500">{m.admin_invite_email_hint()}</span>
		</label>
		<label class="flex flex-col gap-1 text-sm">
			{m.admin_invite_days()}
			<input
				type="number"
				min="1"
				max="30"
				required
				bind:value={inviteDays}
				class="rounded border border-slate-300 px-3 py-2"
			/>
		</label>
		<div class="flex items-end sm:col-span-2">
			<button
				type="submit"
				disabled={busy}
				class="rounded bg-slate-900 px-4 py-2 font-medium text-white disabled:opacity-50"
			>
				{m.admin_invite_create()}
			</button>
		</div>
	</form>
	{#if inviteUrl}
		<div class="mt-4 rounded border border-amber-300 bg-amber-50 p-3 text-sm">
			<p>{m.admin_invite_link()}</p>
			<div class="mt-2 flex gap-2">
				<input
					readonly
					value={inviteUrl}
					aria-label={m.admin_invite_title()}
					class="min-w-0 flex-1 rounded border border-slate-300 bg-white px-2 py-1 font-mono text-xs"
				/>
				<button type="button" onclick={copyInvite} class="rounded border border-slate-300 px-3">
					{copied ? m.admin_copied() : m.admin_copy()}
				</button>
			</div>
		</div>
	{/if}
</section>

<section aria-labelledby="invites-heading" class="mt-8">
	<h2 id="invites-heading" class="font-semibold">{m.admin_invites_title()}</h2>
	{#if inviteList.length === 0}
		<p class="mt-2 text-sm text-slate-600">{m.admin_invites_empty()}</p>
	{:else}
		<div class="mt-2 overflow-x-auto">
			<table class="w-full text-left text-sm">
				<thead class="text-slate-500">
					<tr>
						<th class="py-2 pr-4 font-medium">{m.field_role()}</th>
						<th class="py-2 pr-4 font-medium">{m.field_email()}</th>
						<th class="py-2 pr-4 font-medium">{m.admin_col_status()}</th>
						<th class="py-2 pr-4 font-medium">{m.admin_col_expires()}</th>
					</tr>
				</thead>
				<tbody>
					{#each inviteList as invite (invite.id)}
						<tr class="border-t border-slate-200">
							<td class="py-2 pr-4">{roleLabel(invite.role)}</td>
							<td class="py-2 pr-4">{invite.email ?? m.admin_invite_anyone()}</td>
							<td class="py-2 pr-4">{inviteStatus(invite)}</td>
							<td class="py-2 pr-4">{formatDate(invite.expiresAt)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</section>

<section aria-labelledby="users-heading" class="mt-8">
	<h2 id="users-heading" class="font-semibold">{m.admin_users_title()}</h2>
	<div class="mt-2 overflow-x-auto">
		<table class="w-full text-left text-sm">
			<thead class="text-slate-500">
				<tr>
					<th class="py-2 pr-4 font-medium">{m.field_name()}</th>
					<th class="py-2 pr-4 font-medium">{m.field_email()}</th>
					<th class="py-2 pr-4 font-medium">{m.field_role()}</th>
					<th class="py-2 pr-4 font-medium">{m.admin_col_status()}</th>
					<th class="py-2 pr-4 font-medium">{m.admin_col_actions()}</th>
				</tr>
			</thead>
			<tbody>
				{#each users as user (user.id)}
					{@const isMe = user.id === data.user.id}
					<tr class="border-t border-slate-200">
						<td class="py-2 pr-4">{user.name}{isMe ? ` (${m.admin_you()})` : ''}</td>
						<td class="py-2 pr-4">{user.email}</td>
						<td class="py-2 pr-4">
							<!-- An admin can't change their own role or ban themselves, so they can't lock
							     themselves out. -->
							{#if isMe || !user.role}
								{user.role ? roleLabel(user.role) : '—'}
							{:else}
								<select
									value={user.role}
									disabled={busy}
									aria-label={m.admin_role_for({ name: user.name })}
									onchange={(event) => setRole(user, event.currentTarget)}
									class="rounded border border-slate-300 px-2 py-1"
								>
									{#each ROLES as role (role)}
										<option value={role}>{roleLabel(role)}</option>
									{/each}
								</select>
							{/if}
						</td>
						<td class="py-2 pr-4">
							{user.banned ? m.admin_user_banned() : m.admin_user_active()}
						</td>
						<td class="py-2 pr-4">
							{#if !isMe}
								<button
									type="button"
									disabled={busy}
									onclick={() => (user.banned ? unban(user) : ban(user))}
									class="rounded border border-slate-300 px-3 py-1 disabled:opacity-50"
								>
									{user.banned ? m.admin_unban() : m.admin_ban()}
								</button>
							{/if}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</section>
