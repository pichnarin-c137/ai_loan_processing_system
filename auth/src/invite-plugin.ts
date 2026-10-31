import { createHash, randomBytes } from 'node:crypto';
import { getCurrentAdapter, type BetterAuthOptions, type BetterAuthPlugin } from 'better-auth';
import { APIError, createAuthEndpoint, sessionMiddleware } from 'better-auth/api';
import * as z from 'zod';
import { INVITE_HEADER, type Invite, type InviteCheck } from './invite-shared.ts';
import { isRole, ROLES, roles } from './roles.ts';

const MAX_LISTED = 200;

type InviteRow = Invite<Date> & { tokenHash: string };

export function hashToken(token: string): string {
	return createHash('sha256').update(token).digest('hex');
}

function canManageInvites(user: object, action: 'create' | 'list'): boolean {
	const role = 'role' in user ? user.role : undefined;
	return isRole(role) && roles[role].authorize({ invite: [action] }).success;
}

/**
 * Invite-only sign-up. An admin creates a link, and only the sha256 of its token is stored.
 * The token sits after the # in the link, so it never reaches server logs or Referer headers.
 */
export const invite = (options: { siteURL: string }) =>
	({
		id: 'invite',
		schema: {
			invite: {
				fields: {
					tokenHash: { type: 'string', required: true, unique: true },
					role: { type: 'string', required: true },
					email: { type: 'string', required: false },
					createdBy: {
						type: 'string',
						required: true,
						references: { model: 'user', field: 'id', onDelete: 'restrict' }
					},
					expiresAt: { type: 'date', required: true },
					usedAt: { type: 'date', required: false },
					usedBy: {
						type: 'string',
						required: false,
						references: { model: 'user', field: 'id', onDelete: 'restrict' }
					},
					createdAt: { type: 'date', required: true }
				}
			}
		},
		endpoints: {
			createInvite: createAuthEndpoint(
				'/invite/create',
				{
					method: 'POST',
					use: [sessionMiddleware],
					body: z.object({
						role: z.enum(ROLES),
						email: z.email().optional(),
						expiresInDays: z.number().int().min(1).max(30).default(7)
					})
				},
				async (ctx) => {
					const { user } = ctx.context.session;
					if (!canManageInvites(user, 'create')) {
						throw new APIError('FORBIDDEN', { message: 'Only admins can create invites' });
					}
					const token = randomBytes(32).toString('base64url');
					const now = new Date();
					const expiresAt = new Date(now.getTime() + ctx.body.expiresInDays * 86_400_000);
					await ctx.context.adapter.create<Omit<InviteRow, 'id'>, InviteRow>({
						model: 'invite',
						data: {
							tokenHash: hashToken(token),
							role: ctx.body.role,
							email: ctx.body.email?.toLowerCase() ?? null,
							createdBy: user.id,
							expiresAt,
							usedAt: null,
							usedBy: null,
							createdAt: now
						}
					});
					return ctx.json({ url: `${options.siteURL}/invite#${token}`, expiresAt });
				}
			),
			// POST, so the token stays out of URLs and access logs.
			checkInvite: createAuthEndpoint(
				'/invite/check',
				{ method: 'POST', body: z.object({ token: z.string().min(1).max(256) }) },
				async (ctx) => {
					const found = await ctx.context.adapter.findOne<InviteRow>({
						model: 'invite',
						where: [{ field: 'tokenHash', value: hashToken(ctx.body.token) }]
					});
					const result: InviteCheck =
						!found || found.usedAt || found.expiresAt <= new Date()
							? { valid: false, role: null, email: null }
							: { valid: true, role: found.role, email: found.email };
					return ctx.json(result);
				}
			),
			listInvites: createAuthEndpoint(
				'/invite/list',
				{ method: 'GET', use: [sessionMiddleware] },
				async (ctx) => {
					if (!canManageInvites(ctx.context.session.user, 'list')) {
						throw new APIError('FORBIDDEN', { message: 'Only admins can list invites' });
					}
					const invites = await ctx.context.adapter.findMany<InviteRow>({
						model: 'invite',
						sortBy: { field: 'createdAt', direction: 'desc' },
						limit: MAX_LISTED
					});
					// Listed field by field, so the token hash (or any column added later) never leaks.
					return ctx.json(
						invites.map(
							({
								id,
								role,
								email,
								createdBy,
								expiresAt,
								usedAt,
								usedBy,
								createdAt
							}): Invite<Date> => ({
								id,
								role,
								email,
								createdBy,
								expiresAt,
								usedAt,
								usedBy,
								createdAt
							})
						)
					);
				}
			)
		},
		rateLimit: [{ pathMatcher: (path) => path === '/invite/check', window: 60, max: 10 }]
	}) satisfies BetterAuthPlugin;

function inviteToken(context: { headers?: HeadersInit } | null): string | null {
	return new Headers(context?.headers).get(INVITE_HEADER);
}

/**
 * Every new user goes through here. Sign-up needs a valid invite, which also sets the role;
 * the admin plugin's create-user (and the seed script) is allowed; anything else is refused.
 */
export function inviteDatabaseHooks(): NonNullable<BetterAuthOptions['databaseHooks']> {
	return {
		user: {
			create: {
				before: async (user, context) => {
					if (context?.path === '/admin/create-user') return;
					if (context?.path !== '/sign-up/email') {
						throw new APIError('FORBIDDEN', { message: 'Accounts are created by invite only' });
					}
					// Sign-up runs in a transaction, and this adapter joins it: if creating the user
					// fails, the invite is given back. One UPDATE, so two sign-ups racing on one
					// invite can't both use it.
					const adapter = await getCurrentAdapter(context.context.adapter);
					const claimed = await adapter.update<InviteRow>({
						model: 'invite',
						where: [
							{ field: 'tokenHash', value: hashToken(inviteToken(context) ?? '') },
							{ field: 'usedAt', value: null },
							{ field: 'expiresAt', operator: 'gt', value: new Date() },
							{ field: 'email', value: null, connector: 'OR' },
							{ field: 'email', value: user.email, mode: 'insensitive', connector: 'OR' }
						],
						update: { usedAt: new Date() }
					});
					if (!claimed) {
						throw new APIError('BAD_REQUEST', { message: 'Invite is invalid or expired' });
					}
					return { data: { ...user, role: claimed.role } };
				},
				after: async (user, context) => {
					const token = inviteToken(context);
					if (context?.path !== '/sign-up/email' || !token) return;
					const adapter = await getCurrentAdapter(context.context.adapter);
					await adapter.update<InviteRow>({
						model: 'invite',
						where: [
							{ field: 'tokenHash', value: hashToken(token) },
							{ field: 'usedBy', value: null }
						],
						update: { usedBy: user.id }
					});
				}
			}
		}
	};
}
