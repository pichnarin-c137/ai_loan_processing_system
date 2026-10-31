// Shared with the frontend (import from 'auth/invite'), so it must not import server code.
import type { Role } from './roles.ts';

/** Header that carries the invite token on /sign-up/email. */
export const INVITE_HEADER = 'x-invite-token';

/** What /invite/check returns, so the invite page can say which role the link is for. */
export type InviteCheck = {
	valid: boolean;
	role: Role | null;
	email: string | null;
};

/** An invite without its token hash. The server holds dates; JSON turns them into strings. */
export type Invite<Time = string> = {
	id: string;
	role: Role;
	email: string | null;
	createdBy: string;
	expiresAt: Time;
	usedAt: Time | null;
	usedBy: string | null;
	createdAt: Time;
};
