import { STAFF_ROLES } from 'auth/roles';

const staffRoles: readonly string[] = STAFF_ROLES;

/** Where each role lands after signing in. An unknown role goes to the public home page. */
export function homeFor(role: string | null | undefined): string {
	if (role === 'customer') return '/my';
	if (role === 'admin') return '/admin/users';
	if (role && staffRoles.includes(role)) return '/staff/queue';
	return '/';
}

const ORIGIN = 'http://this-site.invalid';

/** Accepts only a path on this site, so `?next=` can't send anyone to another site. */
export function safeNext(next: string | null | undefined): string | null {
	if (!next?.startsWith('/')) return null;
	// Parsed as the browser will: it drops tabs and newlines and reads \ as /, so a check on the
	// raw text would let `/\t/evil.example` through as `//evil.example`.
	const url = URL.parse(next, ORIGIN);
	return url?.origin === ORIGIN ? url.pathname + url.search + url.hash : null;
}
