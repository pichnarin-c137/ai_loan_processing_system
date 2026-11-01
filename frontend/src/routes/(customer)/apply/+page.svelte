<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { loanOptionsQuery, type ApplicationDetail } from '#lib/api/applications.js';
	import { errorMessages } from '#lib/api/errors.js';
	import FormError from '#lib/components/apply/FormError.svelte';
	import LoanStep from '#lib/components/apply/LoanStep.svelte';
	import WizardProgress from '#lib/components/apply/WizardProgress.svelte';
	import { Button } from '#lib/components/ui/button/index.js';
	import { m } from '#lib/paraglide/messages.js';
	import { createQuery } from '@tanstack/svelte-query';

	const options = createQuery(() => loanOptionsQuery());

	function saved(detail: ApplicationDetail) {
		// eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
		void goto(`${resolve('/(customer)/apply/[id]', { id: detail.id })}?step=about`);
	}
</script>

<svelte:head><title>{m.apply_title()}</title></svelte:head>

<div class="grid gap-6">
	<h1 class="text-xl font-semibold">{m.apply_title()}</h1>
	<WizardProgress step="loan" />
	{#if options.data}
		<LoanStep application={null} options={options.data} onSaved={saved} />
	{:else if options.isError}
		<FormError message={errorMessages(options.error).form} />
		<Button variant="outline" onclick={() => options.refetch()}>{m.try_again()}</Button>
	{:else}
		<p class="text-muted-foreground">{m.loading()}</p>
	{/if}
</div>
