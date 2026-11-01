<script lang="ts">
	import { applicationKeys, uploadDocument, type DocumentOut } from '#lib/api/applications.js';
	import { ApiError, errorMessages } from '#lib/api/errors.js';
	import { formatBytes, MAX_UPLOAD_BYTES, shrinkImage } from '#lib/applications/photo.js';
	import { docTypeLabel, type DocType } from '#lib/applications/status.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale } from '#lib/paraglide/runtime.js';
	import { createMutation, useQueryClient } from '@tanstack/svelte-query';

	interface Props {
		applicationId: string;
		docType: DocType;
		/** The active document in this slot, if one has been uploaded. */
		document: DocumentOut | undefined;
	}

	let { applicationId, docType, document }: Props = $props();

	const locale = getLocale();
	const queryClient = useQueryClient();
	let cameraInput = $state<HTMLInputElement>();
	let fileInput = $state<HTMLInputElement>();

	const mutation = createMutation(() => ({
		mutationFn: async (file: File) => {
			// Phone photos are shrunk (and lose their EXIF location) before they leave the device.
			const upload = await shrinkImage(file);
			if (upload.size > MAX_UPLOAD_BYTES) {
				throw new ApiError(413, { detail: { code: 'file_too_large' } });
			}
			return uploadDocument(applicationId, docType, upload);
		},
		// Stay in "Uploading…" until the application shows the new document.
		onSuccess: () =>
			queryClient.invalidateQueries({ queryKey: applicationKeys.detail(applicationId) })
	}));

	const label = $derived(docTypeLabel(docType));
	const failure = $derived(mutation.error ? errorMessages(mutation.error).form : null);
	// A dropped connection or a storage outage may work the second time; a refused file won't.
	const canRetry = $derived(
		mutation.error !== null &&
			(!(mutation.error instanceof ApiError) || mutation.error.status >= 500)
	);

	function picked(event: Event & { currentTarget: HTMLInputElement }) {
		const file = event.currentTarget.files?.[0];
		// Clear the input, so picking the same file again still fires a change.
		event.currentTarget.value = '';
		if (file) mutation.mutate(file);
	}

	function retry() {
		if (mutation.variables) mutation.mutate(mutation.variables);
	}
</script>

<li class="grid gap-3 rounded-lg border p-4">
	<div class="flex items-baseline justify-between gap-3">
		<h3 class="font-medium">{label}</h3>
		<p class="text-sm" aria-live="polite">
			{#if mutation.isPending}
				<span class="text-muted-foreground">{m.upload_uploading()}</span>
			{:else if document}
				<span class="text-emerald-700">✓ {m.upload_done()}</span>
			{/if}
		</p>
	</div>

	{#if document && !mutation.isPending}
		<p class="text-sm text-muted-foreground">
			{formatBytes(document.size_bytes, locale)} · {m.upload_pages({ count: document.page_count })}
		</p>
	{/if}

	{#if failure && !mutation.isPending}
		<!-- If a replacement fails, the earlier file stays in the slot, so it still shows above. -->
		<p class="text-sm text-destructive" role="alert">{failure}</p>
	{/if}

	<input
		bind:this={cameraInput}
		type="file"
		accept="image/*"
		capture="environment"
		hidden
		onchange={picked}
	/>
	<input
		bind:this={fileInput}
		type="file"
		accept="application/pdf,image/jpeg,image/png"
		hidden
		onchange={picked}
	/>

	{#if !mutation.isPending}
		<div class="flex flex-wrap gap-2">
			{#if canRetry}
				<Button type="button" size="sm" onclick={retry}>{m.try_again()}</Button>
			{/if}
			{#if document}
				<Button
					type="button"
					size="sm"
					variant="outline"
					aria-label="{m.upload_replace()}: {label}"
					onclick={() => fileInput?.click()}
				>
					{m.upload_replace()}
				</Button>
			{:else}
				<Button
					type="button"
					size="sm"
					variant="outline"
					aria-label="{m.upload_take_photo()}: {label}"
					onclick={() => cameraInput?.click()}
				>
					{m.upload_take_photo()}
				</Button>
				<Button
					type="button"
					size="sm"
					variant="outline"
					aria-label="{m.upload_choose_file()}: {label}"
					onclick={() => fileInput?.click()}
				>
					{m.upload_choose_file()}
				</Button>
			{/if}
		</div>
	{/if}
</li>
