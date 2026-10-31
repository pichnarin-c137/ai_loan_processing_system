import type { Invite, InviteCheck } from 'auth/invite';
import { ac, roles, type Role } from 'auth/roles';
import { adminClient, jwtClient } from 'better-auth/client/plugins';
import { createAuthClient } from 'better-auth/svelte';

export { INVITE_HEADER, type Invite, type InviteCheck } from 'auth/invite';

/** Better Auth in the browser. Same origin: Vite (and Caddy in production) send /api/auth to the auth service. */
export const authClient = createAuthClient({
	plugins: [adminClient({ ac, roles }), jwtClient()]
});

/** The invite endpoints come from our own plugin, so the client has no typed methods for them. */
export const invites = {
	check: (token: string) =>
		authClient.$fetch<InviteCheck>('/invite/check', { method: 'POST', body: { token } }),
	create: (body: { role: Role; email?: string; expiresInDays: number }) =>
		authClient.$fetch<{ url: string; expiresAt: string }>('/invite/create', {
			method: 'POST',
			body
		}),
	list: () => authClient.$fetch<Invite[]>('/invite/list', { method: 'GET' })
};
