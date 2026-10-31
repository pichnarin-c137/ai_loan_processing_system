<script lang="ts">
	import { m } from '#lib/paraglide/messages.js';
	import { getLocale } from '#lib/paraglide/runtime.js';
	import { releases, repoUrl } from '#lib/whats-new.js';

	const locale = getLocale();

	// Dates are calendar days, so format them in UTC or they shift a day west of Greenwich.
	const formatDay = (day: string) =>
		new Date(day).toLocaleDateString(locale, { dateStyle: 'long', timeZone: 'UTC' });
</script>

<h1 class="text-xl font-semibold">{m.whats_new_title()}</h1>
<p class="mt-1 text-sm text-slate-600">{m.whats_new_intro()}</p>

<ol class="mt-6 flex max-w-2xl flex-col gap-4">
	{#each releases as release (release.prs.join())}
		<li class="rounded-lg bg-white p-4 shadow-sm">
			<h2 class="font-semibold">{release.title[locale]}</h2>
			<p class="mt-1 flex flex-wrap gap-x-2 text-sm text-slate-500">
				<time datetime={release.date}>{formatDay(release.date)}</time>
				{#each release.prs as pr (pr)}
					<a href="{repoUrl}/pull/{pr}" rel="external noreferrer" class="underline">
						{m.whats_new_pr({ number: pr })}
					</a>
				{/each}
			</p>
			<ul class="mt-3 list-disc space-y-1 pl-5 text-sm">
				{#each release.items as item, i (i)}
					<li>{item[locale]}</li>
				{/each}
			</ul>
		</li>
	{/each}
</ol>
