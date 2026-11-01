import { m } from '#lib/paraglide/messages.js';
import { describe, expect, it } from 'vitest';
import { missingLabel, statusLabel, timelineIndex, timelineSteps } from './status';
import { firstIncompleteStep } from './wizard';
import type { ApplicationDetail } from '#lib/api/applications.js';

describe('customer status', () => {
	it('gives every status a label', () => {
		expect(statusLabel('checking')).toBe(m.status_checking());
		expect(statusLabel('not_approved')).toBe(m.status_not_approved());
	});

	it('places each status on the timeline', () => {
		expect(timelineIndex('draft')).toBe(0);
		expect(timelineIndex('checking')).toBe(1);
		expect(timelineIndex('under_review')).toBe(2);
		expect(timelineIndex('action_needed')).toBe(2);
		expect(timelineIndex('approved')).toBe(timelineSteps.length - 1);
		expect(timelineIndex('not_approved')).toBe(timelineSteps.length - 1);
	});

	it('names missing items', () => {
		expect(missingLabel('applicant')).toBe(m.review_missing_applicant());
		expect(missingLabel('payslip')).toBe(m.doc_payslip());
	});
});

describe('firstIncompleteStep', () => {
	const draft = {
		applicant: null,
		missing: ['applicant', 'national_id']
	} as unknown as ApplicationDetail;

	it('reopens a draft where it is still missing something', () => {
		expect(firstIncompleteStep(draft)).toBe('about');
		expect(firstIncompleteStep({ ...draft, applicant: {}, missing: ['payslip'] } as never)).toBe(
			'documents'
		);
		expect(firstIncompleteStep({ ...draft, applicant: {}, missing: [] } as never)).toBe('review');
	});
});
