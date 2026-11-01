<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { applicationQuery, loanOptionsQuery } from '#lib/api/applications.js';
	import { errorMessages } from '#lib/api/errors.js';
	import { firstIncompleteStep, isWizardStep, type WizardStep } from '#lib/applications/wizard.js';
	import AboutYouStep from '#lib/components/apply/AboutYouStep.svelte';
	import DocumentsStep from '#lib/components/apply/DocumentsStep.svelte';
	import FormError from '#lib/components/apply/FormError.svelte';
	import LoanStep from '#lib/components/apply/LoanStep.svelte';
	import ReviewStep from '#lib/components/apply/ReviewStep.svelte';
	import WizardProgress from '#lib/components/apply/WizardProgress.svelte';
	import { Button } from '#lib/components/ui/button/index.js';
	import { m } from '#lib/paraglide/messages.js';
	import { createQuery } from '@tanstack/svelte-query';
	import type { PageProps } from './$types';

	let { params }: PageProps = $props();

	const application = createQuery(() => applicationQuery(params.id));
	const options = createQuery(() => loanOptionsQuery());

	const requested = $derived(page.url.searchParams.get('step'));
	const step = $derived<WizardStep | null>(
		isWizardStep(requested)
			? requested
			: application.data
				? firstIncompleteStep(application.data)
				: null
	);
	const failed = $derived(application.error ?? options.error);

	function goTo(next: WizardStep) {
		// eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
		void goto(`${resolve('/(customer)/apply/[id]', { id: params.id })}?step=${next}`);
	}

	// Called both by the effect below and by a successful submit, so navigate only once.
	let leaving = false;
	function showTracker() {
		if (leaving) return;
		leaving = true;
		void goto(resolve('/(customer)/my/[id]', { id: params.id }), { replace: true });
	}

	// A submitted application can't be edited, so send the customer to its tracker.
	$effect(() => {
		if (application.data && application.data.status !== 'draft') showTracker();
	});
</script>

<svelte:head><title>{m.apply_title()}</title></svelte:head>

<div class="grid gap-6">
	<h1 class="text-xl font-semibold">{m.apply_title()}</h1>
	{#if application.data && options.data && step && application.data.status === 'draft'}
		<WizardProgress {step} />
		{#key `${application.data.id}:${step}`}
			{#if step === 'loan'}
				<LoanStep
					application={application.data}
					options={options.data}
					onSaved={() => {
						goTo('about');
					}}
				/>
			{:else if step === 'about'}
				<AboutYouStep
					application={application.data}
					onSaved={() => {
						goTo('documents');
					}}
					onBack={() => {
						goTo('loan');
					}}
				/>
			{:else if step === 'documents'}
				<DocumentsStep
					application={application.data}
					onNext={() => {
						goTo('review');
					}}
					onBack={() => {
						goTo('about');
					}}
				/>
			{:else}
				<ReviewStep application={application.data} onEdit={goTo} onSubmitted={showTracker} />
			{/if}
		{/key}
	{:else if failed}
		<FormError message={errorMessages(failed).form} />
		<Button
			variant="outline"
			onclick={() => {
				void application.refetch();
				void options.refetch();
			}}>{m.try_again()}</Button
		>
	{:else}
		<p class="text-muted-foreground">{m.loading()}</p>
	{/if}
</div>
