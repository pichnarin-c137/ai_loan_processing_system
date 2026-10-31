import { describe, expect, it } from 'vitest';
import { homeFor, safeNext } from './navigation';

describe('homeFor', () => {
	it('sends each role to its start page', () => {
		expect(homeFor('customer')).toBe('/my');
		expect(homeFor('admin')).toBe('/admin/users');
		for (const role of ['officer', 'analyst', 'risk', 'manager', 'committee']) {
			expect(homeFor(role)).toBe('/staff/queue');
		}
	});

	it('sends an unknown or missing role to the home page', () => {
		expect(homeFor('superuser')).toBe('/');
		expect(homeFor(null)).toBe('/');
		expect(homeFor(undefined)).toBe('/');
	});
});

describe('safeNext', () => {
	it('keeps a path on this site', () => {
		expect(safeNext('/staff/queue')).toBe('/staff/queue');
		expect(safeNext('/my?tab=1#top')).toBe('/my?tab=1#top');
	});

	it('refuses anything that could leave the site', () => {
		for (const next of [
			'https://evil.example',
			'//evil.example',
			'/\\evil.example',
			'/\t/evil.example',
			'/\n/evil.example',
			'/\r\n/evil.example',
			'\\/evil.example',
			'javascript:alert(1)',
			'staff/queue',
			'',
			null,
			undefined
		]) {
			expect(safeNext(next)).toBeNull();
		}
	});
});
