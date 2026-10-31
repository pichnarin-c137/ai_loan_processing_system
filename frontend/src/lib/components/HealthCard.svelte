<script lang="ts">
	import type { ServiceName, ServiceStatus } from '#lib/api/health.js';
	import { m } from '#lib/paraglide/messages.js';

	interface Props {
		/** undefined while a check is running. */
		services: ServiceStatus[] | undefined;
		onretry: () => void;
	}

	let { services, onretry }: Props = $props();

	const labels: Record<ServiceName, () => string> = {
		api: m.health_api,
		database: m.health_database,
		redis: m.health_redis,
		storage: m.health_storage,
		auth: m.health_auth
	};

	const summary = $derived(
		services === undefined ? 'checking' : services.every((service) => service.ok) ? 'ok' : 'down'
	);
	const summaryText = {
		checking: m.health_checking,
		ok: m.health_all_ok,
		down: m.health_some_down
	};
	const summaryTone = { checking: 'text-slate-600', ok: 'text-emerald-700', down: 'text-red-700' };
</script>

<section
	aria-labelledby="health-title"
	class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
>
	<div class="flex items-center justify-between gap-4">
		<h1 id="health-title" class="text-lg font-semibold">{m.health_title()}</h1>
		<button
			type="button"
			onclick={onretry}
			disabled={services === undefined}
			class="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50"
		>
			{m.health_retry()}
		</button>
	</div>

	<!-- One live region that stays mounted, so screen readers announce each change of its text. -->
	<p role="status" class={['mt-2 text-sm', summaryTone[summary]]}>{summaryText[summary]()}</p>
	{#if services !== undefined}
		<ul class="mt-4 divide-y divide-slate-100">
			{#each services as service (service.name)}
				<li class="flex items-center justify-between py-2">
					<span>{labels[service.name]()}</span>
					<span
						class={[
							'rounded-full px-2 py-0.5 text-xs font-medium',
							service.ok ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
						]}
					>
						{service.ok ? m.health_ok() : m.health_down()}
					</span>
				</li>
			{/each}
		</ul>
	{/if}
</section>
