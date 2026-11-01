<script lang="ts">
	import {
		applicationKeys,
		storeApplication,
		submitApplication,
		type ApplicationDetail
	} from '#lib/api/applications.js';
	import { errorCode, errorMessages } from '#lib/api/errors.js';
	import { docTypeLabel, missingLabel } from '#lib/applications/status.js';
	import type { WizardStep } from '#lib/applications/wizard.js';
	import * as Alert from '#lib/components/ui/alert/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Checkbox } from '#lib/components/ui/checkbox/index.js';
	import { Label } from '#lib/components/ui/label/index.js';
	import { formatMoney } from '#lib/money.js';
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale } from '#lib/paraglide/runtime.js';
	import { createMutation, useQueryClient } from '@tanstack/svelte-query';
	import FormError from './FormError.svelte';

	interface Props {
		application: ApplicationDetail;
		onEdit: (step: WizardStep) => void;
		onSubmitted: (application: ApplicationDetail) => void;
	}

	let { application, onEdit, onSubmitted }: Props = $props();

	const locale = getLocale();
	const queryClient = useQueryClient();
	// A date of birth is a calendar day (`2001-04-17`): format it in UTC so no time zone shifts it.
	const formatDay = (day: string) =>
		new Intl.DateTimeFormat(locale, { dateStyle: 'long', timeZone: 'UTC' }).format(new Date(day));
	let confirmed = $state(false);

	const mutation = createMutation(() => ({
		mutationFn: () => submitApplication(application.id),
		onSuccess: (detail: ApplicationDetail) => {
			storeApplication(queryClient, detail);
			onSubmitted(detail);
		},
		onError: (error: Error) => {
			// Something changed since this page loaded: fetch the application to show what's missing.
			if (errorCode(error) === 'incomplete') {
				void queryClient.invalidateQueries({ queryKey: applicationKeys.detail(application.id) });
			}
		}
	}));

	const failure = $derived(mutation.error ? errorMessages(mutation.error).form : null);
	const applicant = $derived(application.applicant);
	const product = $derived(
		application.product === 'personal' ? m.product_personal() : m.product_small_business()
	);
</script>

{#snippet section(title: string, step: WizardStep)}
	<div class="flex items-center justify-between">
		<h3 class="font-medium">{title}</h3>
		<Button
			type="button"
			variant="link"
			size="sm"
			onclick={() => {
				onEdit(step);
			}}
		>
			{m.review_edit()}<span class="sr-only">: {title}</span>
		</Button>
	</div>
{/snippet}

{#snippet row(term: string, value: string)}
	<div class="grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-2">
		<dt class="text-muted-foreground">{term}</dt>
		<dd class="break-words">{value}</dd>
	</div>
{/snippet}

<div class="grid gap-5">
	<p class="text-sm text-muted-foreground">{m.review_intro()}</p>

	<section class="grid gap-2 rounded-lg border p-4">
		{@render section(m.apply_step_loan(), 'loan')}
		<dl class="grid gap-1 text-sm">
			{@render row(m.loan_product(), product)}
			{@render row(m.loan_amount(), formatMoney(application.amount, application.currency, locale))}
			{@render row(m.loan_term(), m.term_months({ count: application.term_months }))}
			{@render row(m.loan_purpose(), application.purpose)}
		</dl>
	</section>

	<section class="grid gap-2 rounded-lg border p-4">
		{@render section(m.apply_step_about(), 'about')}
		{#if applicant}
			<dl class="grid gap-1 text-sm">
				{#if applicant.full_name_km}{@render row(m.about_name_km(), applicant.full_name_km)}{/if}
				{#if applicant.full_name_en}{@render row(m.about_name_en(), applicant.full_name_en)}{/if}
				{@render row(m.about_dob(), formatDay(applicant.dob))}
				{@render row(m.about_national_id(), applicant.national_id)}
				{@render row(m.about_phone(), applicant.phone)}
			</dl>
		{/if}
	</section>

	<section class="grid gap-2 rounded-lg border p-4">
		{@render section(m.apply_step_documents(), 'documents')}
		<ul class="grid gap-1 text-sm">
			{#each application.documents as doc (doc.id)}
				<li>✓ {docTypeLabel(doc.doc_type)}</li>
			{/each}
		</ul>
	</section>

	{#if application.missing.length > 0}
		<Alert.Root variant="destructive">
			<Alert.Title>{m.review_missing()}</Alert.Title>
			<Alert.Description>
				<ul class="list-disc ps-5">
					{#each application.missing as item (item)}
						<li>{missingLabel(item)}</li>
					{/each}
				</ul>
			</Alert.Description>
		</Alert.Root>
	{/if}

	<Label class="flex items-start gap-3 rounded-lg border p-3 font-normal">
		<Checkbox bind:checked={confirmed} class="mt-0.5" />
		{m.review_confirm()}
	</Label>

	<FormError message={failure} />

	<Button
		type="button"
		class="w-full"
		disabled={!confirmed || application.missing.length > 0 || mutation.isPending}
		onclick={() => {
			mutation.mutate();
		}}
	>
		{mutation.isPending ? m.review_submitting() : m.review_submit()}
	</Button>
</div>
