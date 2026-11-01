<script lang="ts">
	import { Label } from '#lib/components/ui/label/index.js';
	import type { Snippet } from 'svelte';

	interface Props {
		id: string;
		label: string;
		hint?: string | undefined;
		error?: string | undefined;
		/** Renders the control, with the ids of the hint and error for aria-describedby. */
		children: Snippet<[{ describedBy: string | undefined; invalid: boolean }]>;
	}

	let { id, label, hint, error, children }: Props = $props();

	const describedBy = $derived(
		[hint ? `${id}-hint` : '', error ? `${id}-error` : ''].filter((part) => part).join(' ') ||
			undefined
	);
</script>

<div class="grid gap-1.5">
	<Label for={id}>{label}</Label>
	{@render children({ describedBy, invalid: Boolean(error) })}
	{#if hint}
		<p id="{id}-hint" class="text-sm text-muted-foreground">{hint}</p>
	{/if}
	{#if error}
		<p id="{id}-error" class="text-sm text-destructive">{error}</p>
	{/if}
</div>
