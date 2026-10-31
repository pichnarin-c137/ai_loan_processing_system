<script lang="ts">
	import { onMount } from 'svelte';
	import { resolve } from '$app/paths';
	import { fetchHealth, type ServiceStatus } from '#lib/api/health.js';
	import HealthCard from '#lib/components/HealthCard.svelte';
	import { m } from '#lib/paraglide/messages.js';

	let services = $state<ServiceStatus[]>();

	async function check() {
		services = undefined;
		services = await fetchHealth();
	}

	onMount(() => {
		void check();
	});
</script>

<main class="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
	<HealthCard {services} onretry={() => void check()} />
	<nav class="mt-6 flex gap-4 text-sm text-blue-700 underline">
		<a href={resolve('/(customer)/my')}>{m.nav_my()}</a>
		<a href={resolve('/(staff)/staff/queue')}>{m.staff_portal()}</a>
	</nav>
</main>
