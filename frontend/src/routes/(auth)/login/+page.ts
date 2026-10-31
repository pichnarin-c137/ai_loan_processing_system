import { redirect } from '@sveltejs/kit';
import { currentUser } from '#lib/auth/guards.js';
import { homeFor } from '#lib/auth/navigation.js';
import type { PageLoad } from './$types';

// Someone who is already signed in goes straight to their start page.
export const load: PageLoad = async () => {
	const user = await currentUser();
	if (user) redirect(307, homeFor(user.role));
};
