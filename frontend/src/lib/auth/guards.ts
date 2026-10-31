import { redirect } from '@sveltejs/kit';
import { isRole, type Role } from 'auth/roles';
import { authClient } from './client';
import { homeFor } from './navigation';

export interface SignedInUser {
	id: string;
	name: string;
	email: string;
	role: Role;
}

/** The signed-in user, or null. A user with a role this app doesn't know counts as signed out. */
export async function currentUser(): Promise<SignedInUser | null> {
	const { data } = await authClient.getSession();
	if (!data || !isRole(data.user.role)) return null;
	const { id, name, email, role } = data.user;
	return { id, name, email, role };
}

/**
 * For a route group's +layout.ts. It only hides pages from the wrong roles; the API checks the
 * role again on every call. `url` is read only when redirecting: SvelteKit reruns a load whenever
 * a URL property it read changes, and this one should run once per visit to the group.
 */
export async function requireRole(
	url: URL,
	allowed: readonly Role[]
): Promise<{ user: SignedInUser }> {
	const user = await currentUser();
	if (!user) redirect(307, `/login?next=${encodeURIComponent(url.pathname + url.search)}`);
	if (!allowed.includes(user.role)) redirect(307, homeFor(user.role));
	return { user };
}
