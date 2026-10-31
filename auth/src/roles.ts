import { createAccessControl } from 'better-auth/plugins/access';

// Shared with the frontend (import from 'auth/roles'), so both use the same role list.
export const ROLES = [
	'customer',
	'officer',
	'analyst',
	'risk',
	'manager',
	'committee',
	'admin'
] as const;
export type Role = (typeof ROLES)[number];

export const STAFF_ROLES = [
	'officer',
	'analyst',
	'risk',
	'manager',
	'committee'
] as const satisfies readonly Role[];

export function isRole(value: unknown): value is Role {
	return typeof value === 'string' && (ROLES as readonly string[]).includes(value);
}

// Only the actions listed here exist. Admins can't impersonate or delete users or change
// their email: deleting a user would orphan the audit references to them.
const statement = {
	user: ['create', 'list', 'get', 'set-role', 'ban', 'set-password'],
	session: ['list', 'revoke'],
	invite: ['create', 'list']
} as const;

export const ac = createAccessControl(statement);

const noAdminAccess = ac.newRole({});

export const roles = {
	customer: noAdminAccess,
	officer: noAdminAccess,
	analyst: noAdminAccess,
	risk: noAdminAccess,
	manager: noAdminAccess,
	committee: noAdminAccess,
	admin: ac.newRole({
		user: ['create', 'list', 'get', 'set-role', 'ban', 'set-password'],
		session: ['list', 'revoke'],
		invite: ['create', 'list']
	})
} satisfies Record<Role, unknown>;
