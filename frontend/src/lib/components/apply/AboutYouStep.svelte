<script lang="ts">
	import {
		saveApplicant,
		storeApplication,
		type ApplicantIn,
		type ApplicationDetail
	} from '#lib/api/applications.js';
	import { errorMessages } from '#lib/api/errors.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import { m } from '#lib/paraglide/messages.js';
	import { createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { untrack } from 'svelte';
	import Field from './Field.svelte';
	import FormError from './FormError.svelte';

	interface Props {
		application: ApplicationDetail;
		onSaved: (application: ApplicationDetail) => void;
		onBack: () => void;
	}

	let { application, onSaved, onBack }: Props = $props();

	const queryClient = useQueryClient();
	// The form starts from the saved draft; the parent remounts it for another application.
	const saved = untrack(() => application.applicant);

	let nameKm = $state(saved?.full_name_km ?? '');
	let nameEn = $state(saved?.full_name_en ?? '');
	let dob = $state(saved?.dob ?? '');
	let nationalId = $state(saved?.national_id ?? '');
	let phone = $state(saved?.phone ?? '');
	let checks = $state<{ form: string | null; fields: Record<string, string> }>({
		form: null,
		fields: {}
	});

	const mutation = createMutation(() => ({
		mutationFn: (body: ApplicantIn) => saveApplicant(application.id, body),
		onSuccess: (detail: ApplicationDetail) => {
			storeApplication(queryClient, detail);
			onSaved(detail);
		}
	}));

	const server = $derived(mutation.error ? errorMessages(mutation.error) : null);
	const errors = $derived({ ...server?.fields, ...checks.fields });
	const formError = $derived(checks.form ?? server?.form);

	function submit(event: SubmitEvent) {
		event.preventDefault();
		mutation.reset();
		const fields: Record<string, string> = {};
		if (!dob) fields.dob = m.err_required();
		if (!nationalId.trim()) fields.national_id = m.err_required();
		if (!phone.trim()) fields.phone = m.err_required();
		const noName = !nameKm.trim() && !nameEn.trim();
		checks = { form: noName ? m.err_name_required() : null, fields };
		if (noName || Object.keys(fields).length > 0) return;
		mutation.mutate({
			full_name_km: nameKm.trim() || null,
			full_name_en: nameEn.trim() || null,
			dob,
			national_id: nationalId.trim(),
			phone: phone.trim()
		});
	}
</script>

<form class="grid gap-5" onsubmit={submit} novalidate>
	<p class="text-sm text-muted-foreground">{m.about_name_hint()}</p>

	<Field id="full_name_km" label={m.about_name_km()} error={errors.full_name_km}>
		{#snippet children({ describedBy, invalid })}
			<Input
				id="full_name_km"
				bind:value={nameKm}
				lang="km"
				maxlength={100}
				autocomplete="off"
				aria-describedby={describedBy}
				aria-invalid={invalid}
			/>
		{/snippet}
	</Field>

	<Field id="full_name_en" label={m.about_name_en()} error={errors.full_name_en}>
		{#snippet children({ describedBy, invalid })}
			<Input
				id="full_name_en"
				bind:value={nameEn}
				maxlength={100}
				autocomplete="name"
				aria-describedby={describedBy}
				aria-invalid={invalid}
			/>
		{/snippet}
	</Field>

	<Field id="dob" label={m.about_dob()} error={errors.dob}>
		{#snippet children({ describedBy, invalid })}
			<Input
				id="dob"
				type="date"
				bind:value={dob}
				autocomplete="bday"
				aria-describedby={describedBy}
				aria-invalid={invalid}
			/>
		{/snippet}
	</Field>

	<Field
		id="national_id"
		label={m.about_national_id()}
		hint={m.about_national_id_hint()}
		error={errors.national_id}
	>
		{#snippet children({ describedBy, invalid })}
			<Input
				id="national_id"
				bind:value={nationalId}
				inputmode="numeric"
				autocomplete="off"
				aria-describedby={describedBy}
				aria-invalid={invalid}
			/>
		{/snippet}
	</Field>

	<Field id="phone" label={m.about_phone()} hint={m.about_phone_hint()} error={errors.phone}>
		{#snippet children({ describedBy, invalid })}
			<Input
				id="phone"
				type="tel"
				bind:value={phone}
				autocomplete="tel"
				aria-describedby={describedBy}
				aria-invalid={invalid}
			/>
		{/snippet}
	</Field>

	<FormError message={formError} />

	<div class="grid grid-cols-2 gap-3">
		<Button type="button" variant="outline" onclick={onBack}>{m.apply_back()}</Button>
		<Button type="submit" disabled={mutation.isPending}>
			{mutation.isPending ? m.apply_saving() : m.apply_next()}
		</Button>
	</div>
</form>
