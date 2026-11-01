import { m } from '#lib/paraglide/messages.js';

/** A non-2xx answer from the API, with its parsed JSON body. */
export class ApiError extends Error {
	constructor(
		readonly status: number,
		readonly body: unknown
	) {
		super(`API answered ${String(status)}`);
		this.name = 'ApiError';
	}
}

/** Where a message belongs: on a form field (by its API name), or on the whole form. */
export interface ErrorMessages {
	form: string | null;
	fields: Record<string, string>;
}

interface FieldIssue {
	loc: (string | number)[];
	type: string;
	ctx?: Record<string, unknown>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null;
}

function fieldIssues(body: unknown): FieldIssue[] | null {
	if (!isRecord(body) || !Array.isArray(body.detail)) return null;
	return body.detail.filter(
		(item): item is FieldIssue =>
			isRecord(item) && Array.isArray(item.loc) && typeof item.type === 'string'
	);
}

/** `{"detail": {"code": "file_too_large"}}` → "file_too_large" */
export function errorCode(error: unknown): string | null {
	if (!(error instanceof ApiError) || !isRecord(error.body)) return null;
	const { detail } = error.body;
	return isRecord(detail) && typeof detail.code === 'string' ? detail.code : null;
}

const codeMessages: Record<string, () => string> = {
	not_found: m.err_not_found,
	not_draft: m.err_not_draft,
	incomplete: m.err_incomplete,
	file_too_large: m.err_file_too_large,
	unsupported_file_type: m.err_unsupported_file_type,
	unreadable_file: m.err_unreadable_file,
	encrypted_pdf: m.err_encrypted_pdf,
	too_many_pages: m.err_too_many_pages,
	doc_type_not_needed: m.err_doc_type_not_needed,
	storage_unavailable: m.err_storage_unavailable,
	no_policy: m.err_no_policy
};

function text(value: unknown): string {
	return typeof value === 'string' || typeof value === 'number' ? String(value) : '';
}

/**
 * One validation problem as a sentence. `formatMax` turns an amount limit (a plain decimal
 * string) into money in the form's currency.
 */
function issueMessage(issue: FieldIssue, formatMax: (max: string) => string): string {
	const ctx = issue.ctx ?? {};
	switch (issue.type) {
		case 'missing':
		case 'string_too_short':
			return m.err_required();
		case 'string_too_long':
			return m.err_too_long({ max: text(ctx.max_length) });
		case 'greater_than':
			return m.err_amount_positive();
		case 'greater_than_equal':
			return m.err_min({ min: text(ctx.ge) });
		case 'less_than_equal':
			return m.err_max({ max: text(ctx.le) });
		case 'amount_decimals':
			return m.err_amount_decimals();
		case 'amount_whole_riel':
			return m.err_amount_whole_riel();
		case 'amount_too_high':
			return m.err_amount_too_high({ max: formatMax(text(ctx.max)) });
		case 'name_required':
			return m.err_name_required();
		case 'age_range':
			return m.err_age_range();
		case 'national_id_format':
			return m.err_national_id_format();
		case 'phone_format':
			return m.err_phone_format();
		default:
			return m.err_invalid();
	}
}

/** Turns anything a request threw into messages to show. */
export function errorMessages(
	error: unknown,
	formatMax: (max: string) => string = (max) => max
): ErrorMessages {
	if (!(error instanceof ApiError)) {
		// fetch rejects with a TypeError when the network is down.
		return { form: error instanceof TypeError ? m.network_error() : m.err_unknown(), fields: {} };
	}
	if (error.status === 401 || error.status === 403) return { form: m.err_session(), fields: {} };

	const issues = error.status === 422 ? fieldIssues(error.body) : null;
	if (issues && issues.length > 0) {
		const fields: Record<string, string> = {};
		let form: string | null = null;
		for (const issue of issues) {
			const message = issueMessage(issue, formatMax);
			// loc is ["body", field] for a field, or ["body"] for a rule across fields.
			const field = issue.loc.length > 1 ? text(issue.loc.at(-1)) : '';
			if (field) fields[field] ??= message;
			else form ??= message;
		}
		return { form, fields };
	}

	const code = errorCode(error);
	const message = code ? codeMessages[code] : undefined;
	return { form: message ? message() : m.err_unknown(), fields: {} };
}
