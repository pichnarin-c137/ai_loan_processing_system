<script lang="ts">
	import * as Alert from '#lib/components/ui/alert/index.js';

	let { message }: { message: string | null | undefined } = $props();
</script>

{#if message}
	<Alert.Root variant="destructive" role="alert">
		<Alert.Description>{message}</Alert.Description>
	</Alert.Root>
{/if}
