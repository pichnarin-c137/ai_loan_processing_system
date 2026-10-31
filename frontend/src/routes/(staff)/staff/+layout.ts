import { STAFF_ROLES } from 'auth/roles';
import { requireRole } from '#lib/auth/guards.js';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = ({ url }) => requireRole(url, STAFF_ROLES);
