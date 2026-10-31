import { describe, expect, it } from 'vitest';
import { releases } from './whats-new';

describe('releases', () => {
	it('lists the newest first', () => {
		const keys = releases.map((r) => `${r.date} ${String(Math.max(...r.prs)).padStart(6, '0')}`);
		expect(keys).toEqual([...keys].sort().reverse());
	});

	it('names each pull request once', () => {
		const prs = releases.flatMap((r) => r.prs);
		expect(new Set(prs).size).toBe(prs.length);
	});

	it('has a real date and at least one item in every language', () => {
		for (const release of releases) {
			expect(release.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
			expect(release.items.length).toBeGreaterThan(0);
			for (const text of [release.title, ...release.items].flatMap((t) => Object.values(t))) {
				expect(text.trim()).not.toBe('');
			}
		}
	});
});
