import type { Role } from 'auth/roles';
import { m } from '#lib/paraglide/messages.js';

const labels: Record<Role, () => string> = {
	customer: m.role_customer,
	officer: m.role_officer,
	analyst: m.role_analyst,
	risk: m.role_risk,
	manager: m.role_manager,
	committee: m.role_committee,
	admin: m.role_admin
};

export const roleLabel = (role: Role): string => labels[role]();
