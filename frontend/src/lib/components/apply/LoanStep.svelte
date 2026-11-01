<script lang="ts">
	import {
		createApplication,
		saveLoan,
		storeApplication,
		type ApplicationDetail,
		type LoanIn,
		type LoanOptions,
		type Product
	} from '#lib/api/applications.js';
	import { errorMessages } from '#lib/api/errors.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import { Label } from '#lib/components/ui/label/index.js';
	import * as RadioGroup from '#lib/components/ui/radio-group/index.js';
	import { cleanAmount, convert, formatMoney, type Currency } from '#lib/money.js';
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale } from '#lib/paraglide/runtime.js';
	import { createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { untrack } from 'svelte';
	import Field from './Field.svelte';
	import FormError from './FormError.svelte';

	interface Props {
		/** null for a new application. */
		application: ApplicationDetail | null;
		options: LoanOptions;
		onSaved: (application: ApplicationDetail) => void;
	}

	let { application, options, onSaved }: Props = $props();

	const locale = getLocale();
	const queryClient = useQueryClient();
	// The form starts from the saved draft; the parent remounts it for another application.
	const saved = untrack(() => application);

	let product = $state<Product>(saved?.product ?? 'personal');
	let currency = $state<Currency>(saved?.currency ?? 'USD');
	let amount = $state(saved ? saved.amount.replace(/\.0+$/, '') : '');
	let term = $state(saved ? String(saved.term_months) : '');
	let purpose = $state(saved?.purpose ?? '');
	let checks = $state<Record<string, string>>({});

	const otherCurrency = $derived<Currency>(currency === 'USD' ? 'KHR' : 'USD');
	const maxAmount = $derived(options.max_amount[currency]);
	const estimate = $derived.by(() => {
		const clean = cleanAmount(amount);
		const converted = clean && convert(clean, currency, otherCurrency, options.khr_per_usd);
		return converted ? formatMoney(converted, otherCurrency, locale) : null;
	});
	const products = [
		{ value: 'personal', label: m.product_personal() },
		{ value: 'small_business', label: m.product_small_business() }
	];
	const currencies = [
		{ value: 'USD', label: m.currency_usd() },
		{ value: 'KHR', label: m.currency_khr() }
	];
	const rate = $derived(
		new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(
			options.khr_per_usd as Intl.StringNumericLiteral
		)
	);

	// Set once a new draft exists, so a second tap before the page changes saves that draft
	// instead of creating another one.
	let createdId = $state<string | null>(null);

	const mutation = createMutation(() => ({
		mutationFn: (body: LoanIn) => {
			const id = application?.id ?? createdId;
			return id ? saveLoan(id, body) : createApplication(body);
		},
		onSuccess: (detail: ApplicationDetail) => {
			createdId = detail.id;
			storeApplication(queryClient, detail);
			onSaved(detail);
		}
	}));

	const server = $derived(
		mutation.error
			? errorMessages(mutation.error, (max) => formatMoney(max, currency, locale))
			: null
	);
	const errors = $derived({ ...server?.fields, ...checks });

	function submit(event: SubmitEvent) {
		event.preventDefault();
		mutation.reset();
		const found: Record<string, string> = {};
		const clean = cleanAmount(amount);
		if (!amount.trim()) found.amount = m.err_required();
		else if (!clean) found.amount = m.err_invalid();
		if (!term.trim()) found.term_months = m.err_required();
		else if (!/^\d+$/.test(term.trim())) found.term_months = m.err_invalid();
		if (!purpose.trim()) found.purpose = m.err_required();
		checks = found;
		if (Object.keys(found).length > 0 || !clean) return;
		mutation.mutate({
			product,
			currency,
			amount: clean,
			term_months: Number(term.trim()),
			purpose: purpose.trim()
		});
	}
</script>

<form class="grid gap-5" onsubmit={submit} novalidate>
	<fieldset class="grid gap-2">
		<legend class="mb-2 text-sm font-medium">{m.loan_product()}</legend>
		<RadioGroup.Root bind:value={product} class="grid gap-2">
			{#each products as { value, label } (value)}
				<Label class="flex items-center gap-3 rounded-lg border p-3 font-normal">
					<RadioGroup.Item {value} />
					{label}
				</Label>
			{/each}
		</RadioGroup.Root>
	</fieldset>

	<fieldset class="grid gap-2">
		<legend class="mb-2 text-sm font-medium">{m.loan_currency()}</legend>
		<RadioGroup.Root bind:value={currency} class="grid grid-cols-2 gap-2">
			{#each currencies as { value, label } (value)}
				<Label class="flex items-center gap-3 rounded-lg border p-3 font-normal">
					<RadioGroup.Item {value} />
					{label}
				</Label>
			{/each}
		</RadioGroup.Root>
	</fieldset>

	<Field
		id="amount"
		label={m.loan_amount()}
		hint={m.loan_amount_limit({ max: formatMoney(maxAmount ?? '0', currency, locale) })}
		error={errors.amount}
	>
		{#snippet children({ describedBy, invalid })}
			<Input
				id="amount"
				bind:value={amount}
				inputmode={currency === 'USD' ? 'decimal' : 'numeric'}
				autocomplete="off"
				aria-describedby={describedBy}
				aria-invalid={invalid}
			/>
		{/snippet}
	</Field>
	{#if estimate}
		<p class="-mt-3 text-sm text-muted-foreground" aria-live="polite">
			{m.loan_amount_estimate({ amount: estimate, rate })}
		</p>
	{/if}

	<Field
		id="term"
		label={m.loan_term()}
		hint={m.loan_term_hint({ min: options.min_term_months, max: options.max_term_months })}
		error={errors.term_months}
	>
		{#snippet children({ describedBy, invalid })}
			<Input
				id="term"
				bind:value={term}
				inputmode="numeric"
				autocomplete="off"
				aria-describedby={describedBy}
				aria-invalid={invalid}
			/>
		{/snippet}
	</Field>

	<Field id="purpose" label={m.loan_purpose()} error={errors.purpose}>
		{#snippet children({ describedBy, invalid })}
			<textarea
				id="purpose"
				bind:value={purpose}
				rows="3"
				maxlength="500"
				aria-describedby={describedBy}
				aria-invalid={invalid}
				class="w-full rounded-lg border border-input bg-transparent px-2.5 py-2 text-base outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:border-destructive md:text-sm"
			></textarea>
		{/snippet}
	</Field>

	<FormError message={server?.form} />

	<Button type="submit" disabled={mutation.isPending} class="w-full">
		{mutation.isPending ? m.apply_saving() : m.apply_next()}
	</Button>
</form>
