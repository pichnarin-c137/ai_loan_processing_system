<script lang="ts">
	import { stepLabel, wizardSteps, type WizardStep } from '#lib/applications/wizard.js';
	import { m } from '#lib/paraglide/messages.js';

	let { step }: { step: WizardStep } = $props();

	const index = $derived(wizardSteps.indexOf(step));
</script>

<div class="grid gap-2">
	<p class="text-sm text-muted-foreground">
		{m.apply_step_of({ current: index + 1, total: wizardSteps.length })} · {stepLabel(step)}
	</p>
	<div class="grid grid-cols-4 gap-1" aria-hidden="true">
		{#each wizardSteps as item, i (item)}
			<span class={['h-1.5 rounded-full', i <= index ? 'bg-primary' : 'bg-muted']}></span>
		{/each}
	</div>
</div>
