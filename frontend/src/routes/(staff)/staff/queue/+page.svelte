<script lang="ts">
	import { m } from '#lib/paraglide/messages.js';
</script>

<h1 class="text-xl font-semibold">{m.nav_queue()}</h1>
<p class="mt-4 rounded-lg border border-dashed border-slate-300 p-6 text-center text-slate-600">
	{m.queue_empty()}
</p>
