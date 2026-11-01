import { describe, expect, it } from 'vitest';
import { cleanAmount, convert, formatMoney } from './money';

describe('formatMoney', () => {
	it('shows dollars with cents and riel without', () => {
		expect(formatMoney('8000', 'USD', 'en')).toBe('$8,000.00');
		expect(formatMoney('32000000', 'KHR', 'en')).toBe('៛32,000,000');
	});

	it('keeps every digit of large amounts, with no float rounding', () => {
		expect(formatMoney('32000000.50', 'USD', 'en')).toBe('$32,000,000.50');
		expect(formatMoney('0.10', 'USD', 'en')).toBe('$0.10');
	});

	it('follows the Khmer locale', () => {
		expect(formatMoney('8000', 'USD', 'km')).toContain('8,000.00');
		expect(formatMoney('32000000', 'KHR', 'km')).toContain('៛');
	});
});

describe('cleanAmount', () => {
	it('strips spaces and thousands separators', () => {
		expect(cleanAmount(' 8,000.50 ')).toBe('8000.50');
		expect(cleanAmount('32 000 000')).toBe('32000000');
	});

	it('refuses anything that is not a plain positive number', () => {
		for (const input of ['', 'abc', '1e5', '-5', '1.2.3', '.']) {
			expect(cleanAmount(input), input).toBeNull();
		}
	});
});

describe('convert', () => {
	it('turns dollars into whole riel at the policy rate', () => {
		expect(convert('8000', 'USD', 'KHR', '4000.00')).toBe('32000000');
		expect(convert('0.01', 'USD', 'KHR', '4000')).toBe('40');
		expect(convert('20000', 'USD', 'KHR', '4100.50')).toBe('82010000');
	});

	it('turns riel into dollars, rounding half up to the cent', () => {
		expect(convert('32000000', 'KHR', 'USD', '4000')).toBe('8000.00');
		expect(convert('100', 'KHR', 'USD', '4000')).toBe('0.03');
		expect(convert('1', 'KHR', 'USD', '4000')).toBe('0.00');
	});

	it('leaves the same currency alone', () => {
		expect(convert('12.50', 'USD', 'USD', '4000')).toBe('12.50');
	});

	it('gives null for bad input', () => {
		expect(convert('abc', 'USD', 'KHR', '4000')).toBeNull();
		expect(convert('10', 'USD', 'KHR', '0')).toBeNull();
	});
});
