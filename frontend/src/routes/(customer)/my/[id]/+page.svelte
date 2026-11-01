<script lang="ts">
	import { resolve } from '$app/paths';
	import { applicationQuery } from '#lib/api/applications.js';
	import { errorMessages } from '#lib/api/errors.js';
	import {
		statusClasses,
		statusLabel,
		timelineIndex,
		timelineLabel,
		timelineSteps
	} from '#lib/applications/status.js';
	import FormError from '#lib/components/apply/FormError.svelte';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { formatMoney } from '#lib/money.js';
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale } from '#lib/paraglide/runtime.js';
	import { createQuery } from '@tanstack/svelte-query';
	import type { PageProps } from './$types';

	let { params }: PageProps = $props();

	const locale = getLocale();
	const application = createQuery(() => applicationQuery(params.id));
	const current = $derived(application.data ? timelineIndex(application.data.status) : 0);
</script>

<svelte:head><title>{m.nav_my()}</title></svelte:head>

<div class="grid gap-6">
	<a href={resolve('/(customer)/my')} class="text-sm text-muted-foreground">← {m.tracker_back()}</a>
	{#if application.data}
		{@const app = application.data}
		<div class="grid gap-2">
			<div class="flex items-center justify-between gap-3">
				<h1 class="text-xl font-semibold">{formatMoney(app.amount, app.currency, locale)}</h1>
				<Badge variant="outline" class={statusClasses(app.status)}>{statusLabel(app.status)}</Badge>
			</div>
			<p class="text-sm text-muted-foreground">
				{app.product === 'personal' ? m.product_personal() : m.product_small_business()} ·
				{m.term_months({ count: app.term_months })}
			</p>
		</div>

		<section class="grid gap-3">
			<h2 class="font-medium">{m.tracker_timeline()}</h2>
			<ol class="grid gap-3">
				{#each timelineSteps as item, i (item)}
					<li class="flex items-center gap-3" aria-current={i === current ? 'step' : undefined}>
						<span
							class={[
								'grid size-6 shrink-0 place-items-center rounded-full border text-xs',
								i < current && 'border-primary bg-primary text-primary-foreground',
								i === current && 'border-primary text-primary',
								i > current && 'text-muted-foreground'
							]}
							aria-hidden="true">{i < current ? '✓' : i + 1}</span
						>
						<span class={i === current ? 'font-medium' : 'text-muted-foreground'}>
							{i === timelineSteps.length - 1 && current === i
								? statusLabel(app.status)
								: timelineLabel(item)}
						</span>
					</li>
				{/each}
			</ol>
		</section>

		{#if app.status === 'draft'}
			<Button href={resolve('/(customer)/apply/[id]', { id: app.id })}>{m.apply_continue()}</Button>
		{/if}
	{:else if application.isError}
		<FormError message={errorMessages(application.error).form} />
	{:else}
		<p class="text-muted-foreground">{m.loading()}</p>
	{/if}
</div>
