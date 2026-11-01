import type { components } from '#lib/api/schema.js';

export type Currency = components['schemas']['Currency'];

/** Decimal places used for each currency. Riel loans are whole riel. */
export const decimals: Record<Currency, number> = { USD: 2, KHR: 0 };

/**
 * `$8,000.00` or `៛32,000,000`, in the reader's language.
 * The amount stays a decimal string from end to end, so it is never rounded through a float.
 */
export function formatMoney(amount: string, currency: Currency, locale: string): string {
	const places = decimals[currency];
	return new Intl.NumberFormat(locale, {
		style: 'currency',
		currency,
		currencyDisplay: 'narrowSymbol',
		minimumFractionDigits: places,
		maximumFractionDigits: places
	}).format(amount as Intl.StringNumericLiteral);
}

const decimalPattern = /^\d+(\.\d+)?$/;

/** Removes the spaces and thousands separators people type. Returns null if what's left isn't a number. */
export function cleanAmount(input: string): string | null {
	const cleaned = input.replace(/[\s,]/g, '');
	return decimalPattern.test(cleaned) ? cleaned : null;
}

/** `value × 10^scale` as a whole number, dropping any digits past `scale`. */
function scaled(value: string, scale: number): bigint {
	const [whole = '0', fraction = ''] = value.split('.');
	return BigInt(whole + fraction.padEnd(scale, '0').slice(0, scale));
}

function divideRounded(numerator: bigint, denominator: bigint): bigint {
	// Rounds half up; both numbers are positive here.
	return (numerator * 2n + denominator) / (denominator * 2n);
}

function toDecimalString(value: bigint, places: number): string {
	if (places === 0) return value.toString();
	const digits = value.toString().padStart(places + 1, '0');
	return `${digits.slice(0, -places)}.${digits.slice(-places)}`;
}

/**
 * Converts an amount at the policy's fixed rate (riel per US dollar), as an estimate for the form.
 * Returns null when the amount or rate isn't a number.
 */
export function convert(
	amount: string,
	from: Currency,
	to: Currency,
	khrPerUsd: string
): string | null {
	if (!decimalPattern.test(amount) || !decimalPattern.test(khrPerUsd)) return null;
	if (from === to) return amount;
	const rate = scaled(khrPerUsd, 2);
	if (rate === 0n) return null;
	if (from === 'USD') {
		// cents × rate×100 = riel × 10^4
		return toDecimalString(divideRounded(scaled(amount, 2) * rate, 10_000n), 0);
	}
	// riel × 10^4 / (rate×100) = cents
	return toDecimalString(divideRounded(scaled(amount, 0) * 10_000n, rate), 2);
}
