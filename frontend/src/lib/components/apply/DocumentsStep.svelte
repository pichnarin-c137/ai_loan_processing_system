<script lang="ts">
	import type { ApplicationDetail } from '#lib/api/applications.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { m } from '#lib/paraglide/messages.js';
	import UploadSlot from './UploadSlot.svelte';

	interface Props {
		application: ApplicationDetail;
		onNext: () => void;
		onBack: () => void;
	}

	let { application, onNext, onBack }: Props = $props();
</script>

<div class="grid gap-5">
	<div class="grid gap-1 text-sm text-muted-foreground">
		<p>{m.documents_intro()}</p>
		<p>{m.documents_formats()}</p>
	</div>

	<ul class="grid gap-3">
		{#each application.required_documents as docType (docType)}
			<UploadSlot
				applicationId={application.id}
				{docType}
				document={application.documents.find((doc) => doc.doc_type === docType)}
			/>
		{/each}
	</ul>

	<div class="grid grid-cols-2 gap-3">
		<Button type="button" variant="outline" onclick={onBack}>{m.apply_back()}</Button>
		<Button type="button" onclick={onNext}>{m.apply_next()}</Button>
	</div>
</div>
