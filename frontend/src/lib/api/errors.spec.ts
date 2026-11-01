import { m } from '#lib/paraglide/messages.js';
import { describe, expect, it } from 'vitest';
import { ApiError, errorCode, errorMessages } from './errors';

const coded = (status: number, code: string) => new ApiError(status, { detail: { code } });

describe('errorCode', () => {
	it('reads detail.code from an API error', () => {
		expect(errorCode(coded(413, 'file_too_large'))).toBe('file_too_large');
	});

	it('gives null for anything else', () => {
		expect(errorCode(new ApiError(500, 'oops'))).toBeNull();
		expect(errorCode(new Error('x'))).toBeNull();
	});
});

describe('errorMessages', () => {
	it('translates known codes', () => {
		expect(errorMessages(coded(413, 'file_too_large'))).toEqual({
			form: m.err_file_too_large(),
			fields: {}
		});
		expect(errorMessages(coded(409, 'not_draft')).form).toBe(m.err_not_draft());
	});

	it('falls back for unknown codes and bodies', () => {
		expect(errorMessages(coded(418, 'teapot')).form).toBe(m.err_unknown());
		expect(errorMessages(new ApiError(500, null)).form).toBe(m.err_unknown());
		expect(errorMessages(new Error('boom')).form).toBe(m.err_unknown());
	});

	it('reports a dropped connection as a network error', () => {
		expect(errorMessages(new TypeError('Failed to fetch')).form).toBe(m.network_error());
	});

	it('asks to sign in again on 401 and 403', () => {
		expect(errorMessages(new ApiError(401, null)).form).toBe(m.err_session());
		expect(errorMessages(new ApiError(403, null)).form).toBe(m.err_session());
	});

	it('puts validation problems on their fields, and cross-field ones on the form', () => {
		const error = new ApiError(422, {
			detail: [
				{ loc: ['body', 'term_months'], type: 'less_than_equal', ctx: { le: 60 } },
				{ loc: ['body', 'amount'], type: 'amount_too_high', ctx: { max: '80000000' } },
				{ loc: ['body', 'amount'], type: 'greater_than', ctx: { gt: 0 } },
				{ loc: ['body', 'purpose'], type: 'string_too_long', ctx: { max_length: 500 } },
				{ loc: ['body', 'phone'], type: 'phone_format' },
				{ loc: ['body', 'dob'], type: 'something_new' },
				{ loc: ['body'], type: 'name_required' }
			]
		});
		expect(errorMessages(error, (max) => `៛${max}`)).toEqual({
			form: m.err_name_required(),
			fields: {
				term_months: m.err_max({ max: '60' }),
				// The first problem on a field wins.
				amount: m.err_amount_too_high({ max: '៛80000000' }),
				purpose: m.err_too_long({ max: '500' }),
				phone: m.err_phone_format(),
				dob: m.err_invalid()
			}
		});
	});
});
