<script lang="ts">
	import { resolve } from '$app/paths';
	import { applicationsQuery } from '#lib/api/applications.js';
	import { errorMessages } from '#lib/api/errors.js';
	import { statusClasses, statusLabel } from '#lib/applications/status.js';
	import FormError from '#lib/components/apply/FormError.svelte';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { formatMoney } from '#lib/money.js';
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale } from '#lib/paraglide/runtime.js';
	import { createQuery } from '@tanstack/svelte-query';

	const locale = getLocale();
	const applications = createQuery(() => applicationsQuery());
	const formatDate = (iso: string) =>
		new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(new Date(iso));
</script>

<svelte:head><title>{m.nav_my()}</title></svelte:head>

<div class="grid gap-4">
	<h1 class="text-xl font-semibold">{m.nav_my()}</h1>
	{#if applications.data && applications.data.length > 0}
		<ul class="grid gap-3">
			{#each applications.data as item (item.id)}
				<li>
					<a
						href={item.status === 'draft'
							? resolve('/(customer)/apply/[id]', { id: item.id })
							: resolve('/(customer)/my/[id]', { id: item.id })}
						class="grid gap-1 rounded-lg border p-4 hover:bg-muted"
					>
						<span class="flex items-center justify-between gap-3">
							<span class="font-medium">{formatMoney(item.amount, item.currency, locale)}</span>
							<Badge variant="outline" class={statusClasses(item.status)}>
								{statusLabel(item.status)}
							</Badge>
						</span>
						<span class="text-sm text-muted-foreground">
							{item.product === 'personal' ? m.product_personal() : m.product_small_business()} ·
							{m.term_months({ count: item.term_months })}
						</span>
						<span class="text-sm text-muted-foreground">
							{item.submitted_at
								? m.my_submitted({ date: formatDate(item.submitted_at) })
								: m.my_started({ date: formatDate(item.created_at) })}
						</span>
					</a>
				</li>
			{/each}
		</ul>
	{:else if applications.data}
		<div class="grid gap-4 rounded-lg border border-dashed p-6 text-center">
			<p class="text-muted-foreground">{m.my_empty()}</p>
			<Button href={resolve('/(customer)/apply')}>{m.nav_apply()}</Button>
		</div>
	{:else if applications.isError}
		<FormError message={errorMessages(applications.error).form} />
		<Button variant="outline" onclick={() => applications.refetch()}>{m.try_again()}</Button>
	{:else}
		<p class="text-muted-foreground">{m.loading()}</p>
	{/if}
</div>
