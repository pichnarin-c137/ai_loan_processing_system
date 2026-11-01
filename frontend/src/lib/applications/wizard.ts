import type { ApplicationDetail } from '#lib/api/applications.js';
import { m } from '#lib/paraglide/messages.js';

export const wizardSteps = ['loan', 'about', 'documents', 'review'] as const;
export type WizardStep = (typeof wizardSteps)[number];

export function isWizardStep(value: string | null): value is WizardStep {
	return wizardSteps.some((step) => step === value);
}

export function stepLabel(step: WizardStep): string {
	switch (step) {
		case 'loan':
			return m.apply_step_loan();
		case 'about':
			return m.apply_step_about();
		case 'documents':
			return m.apply_step_documents();
		case 'review':
			return m.apply_step_review();
	}
}

/** Where to reopen a saved draft: the first step that still has something missing. */
export function firstIncompleteStep(application: ApplicationDetail): WizardStep {
	if (!application.applicant) return 'about';
	if (application.missing.length > 0) return 'documents';
	return 'review';
}
