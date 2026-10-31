<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { m } from '#lib/paraglide/messages.js';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	const links = [{ href: resolve('/(staff)/staff/queue'), label: m.nav_queue }];
</script>

<!-- Staff pages are designed for desktop: a sidebar that becomes a top bar on small screens. -->
<div class="flex flex-1 flex-col md:flex-row">
	<nav
		aria-label={m.staff_portal()}
		class="border-b border-slate-200 bg-white md:w-56 md:border-r md:border-b-0"
	>
		<p class="px-4 pt-4 text-xs font-semibold text-slate-500 uppercase">{m.staff_portal()}</p>
		<ul class="flex gap-1 p-2 md:flex-col">
			{#each links as link (link.href)}
				<li>
					<a
						href={link.href}
						aria-current={page.url.pathname === link.href ? 'page' : undefined}
						class="block rounded px-3 py-2 hover:bg-slate-100 aria-[current=page]:bg-slate-100 aria-[current=page]:font-medium"
					>
						{link.label()}
					</a>
				</li>
			{/each}
		</ul>
	</nav>
	<main class="flex-1 p-6">
		{@render children()}
	</main>
</div>
