import type { components } from '#lib/api/schema.js';
import { m } from '#lib/paraglide/messages.js';

export type CustomerStatus = components['schemas']['CustomerStatus'];
export type DocType = components['schemas']['DocType'];

export function statusLabel(status: CustomerStatus): string {
	switch (status) {
		case 'draft':
			return m.status_draft();
		case 'checking':
			return m.status_checking();
		case 'under_review':
			return m.status_under_review();
		case 'action_needed':
			return m.status_action_needed();
		case 'approved':
			return m.status_approved();
		case 'not_approved':
			return m.status_not_approved();
	}
}

/** Tailwind classes for the status badge. */
export function statusClasses(status: CustomerStatus): string {
	switch (status) {
		case 'draft':
			return 'border-slate-300 bg-white text-slate-700';
		case 'checking':
		case 'under_review':
			return 'border-transparent bg-sky-100 text-sky-900';
		case 'action_needed':
			return 'border-transparent bg-amber-100 text-amber-950';
		case 'approved':
			return 'border-transparent bg-emerald-100 text-emerald-900';
		case 'not_approved':
			return 'border-transparent bg-rose-100 text-rose-900';
	}
}

/** The tracker's four steps, in order. */
export const timelineSteps = ['draft', 'checking', 'under_review', 'decision'] as const;
export type TimelineStep = (typeof timelineSteps)[number];

/** Index of the step the application is on now. */
export function timelineIndex(status: CustomerStatus): number {
	switch (status) {
		case 'draft':
			return 0;
		case 'checking':
			return 1;
		case 'under_review':
		case 'action_needed':
			return 2;
		case 'approved':
		case 'not_approved':
			return 3;
	}
}

export function timelineLabel(step: TimelineStep): string {
	return step === 'decision' ? m.timeline_decision() : statusLabel(step);
}

export function docTypeLabel(docType: DocType): string {
	switch (docType) {
		case 'national_id':
			return m.doc_national_id();
		case 'payslip':
			return m.doc_payslip();
		case 'bank_statement':
			return m.doc_bank_statement();
		case 'business_license':
			return m.doc_business_license();
		case 'other':
			return m.doc_other();
	}
}

/** The API's `missing` list holds "applicant" and document types. */
export function missingLabel(item: string): string {
	if (item === 'applicant') return m.review_missing_applicant();
	return isDocType(item) ? docTypeLabel(item) : item;
}

const docTypes: readonly string[] = [
	'national_id',
	'payslip',
	'bank_statement',
	'business_license',
	'other'
] satisfies DocType[];

function isDocType(value: string): value is DocType {
	return docTypes.includes(value);
}
