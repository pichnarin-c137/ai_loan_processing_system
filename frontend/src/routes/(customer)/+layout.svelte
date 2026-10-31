<script lang="ts">
	import { resolve } from '$app/paths';
	import { m } from '#lib/paraglide/messages.js';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<!-- Customer pages are designed for phones first: one narrow column with a bottom menu. -->
<main class="mx-auto w-full max-w-md flex-1 px-4 py-6">
	{@render children()}
</main>
<nav aria-label={m.nav_customer()} class="sticky bottom-0 border-t border-slate-200 bg-white">
	<ul class="mx-auto flex max-w-md justify-around py-2 text-sm">
		<li><a href={resolve('/')} class="block px-3 py-2">{m.nav_home()}</a></li>
		<li><a href={resolve('/(customer)/my')} class="block px-3 py-2">{m.nav_my()}</a></li>
	</ul>
</nav>
