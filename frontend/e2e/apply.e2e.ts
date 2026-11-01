import { expect, test, type Page, type Route } from '@playwright/test';
import type { components } from '../src/lib/api/schema.js';

type Detail = components['schemas']['ApplicationDetail'];
type DocType = components['schemas']['DocType'];

const now = new Date().toISOString();

/** An unsigned token: the mocked API never checks it, but the app reads its expiry. */
const token = `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 900 }))}.sig`;

/**
 * A small in-memory stand-in for the applications API, so the wizard can run against the
 * built SPA alone. `refuse` makes every upload fail with that error code.
 */
function fakeApi(page: Page, options: { draft?: Partial<Detail>; refuse?: string } = {}) {
	const requests: { method: string; path: string; body: unknown }[] = [];
	let app: Detail | null = options.draft
		? {
				id: 'app-1',
				product: 'personal',
				currency: 'USD',
				amount: '8000.00',
				term_months: 24,
				purpose: 'Sample purpose',
				status: 'draft',
				created_at: now,
				updated_at: now,
				submitted_at: null,
				applicant: null,
				documents: [],
				required_documents: ['national_id', 'payslip', 'bank_statement'],
				missing: [],
				...options.draft
			}
		: null;

	function current(): Detail {
		if (!app) throw new Error('no application yet');
		const have = new Set(app.documents.map((doc) => doc.doc_type));
		app.missing = [
			...(app.applicant ? [] : ['applicant']),
			...app.required_documents.filter((type) => !have.has(type))
		];
		return app;
	}

	async function handle(route: Route) {
		const request = route.request();
		const path = new URL(request.url()).pathname;
		const method = request.method();
		// Uploads send the raw file, not JSON.
		const json: unknown =
			method === 'GET' || path.includes('/documents/') ? null : (request.postDataJSON() as unknown);
		requests.push({ method, path, body: json });

		if (path === '/api/applications' && method === 'POST') {
			const loan = json as Pick<
				Detail,
				'product' | 'currency' | 'amount' | 'term_months' | 'purpose'
			>;
			app = {
				...loan,
				id: 'app-1',
				status: 'draft',
				created_at: now,
				updated_at: now,
				submitted_at: null,
				applicant: null,
				documents: [],
				required_documents: ['national_id', 'payslip', 'bank_statement'],
				missing: []
			};
			return route.fulfill({ status: 201, json: current() });
		}
		if (path === '/api/applications') {
			const list = app ? [current()] : [];
			return route.fulfill({ json: list });
		}
		if (path === '/api/applications/app-1') return route.fulfill({ json: current() });
		if (path === '/api/applications/app-1/applicant') {
			current().applicant = json as Detail['applicant'];
			return route.fulfill({ json: current() });
		}
		const upload = /^\/api\/applications\/app-1\/documents\/(\w+)$/.exec(path);
		if (upload?.[1]) {
			if (options.refuse) {
				return route.fulfill({ status: 415, json: { detail: { code: options.refuse } } });
			}
			const docType = upload[1] as DocType;
			const doc = {
				id: `doc-${docType}`,
				doc_type: docType,
				content_type: 'application/pdf',
				size_bytes: request.postDataBuffer()?.length ?? 0,
				page_count: 1,
				uploaded_at: now
			};
			const detail = current();
			detail.documents = [...detail.documents.filter((d) => d.doc_type !== docType), doc];
			return route.fulfill({ status: 201, json: doc });
		}
		if (path === '/api/applications/app-1/submit') {
			Object.assign(current(), { status: 'checking', submitted_at: now });
			return route.fulfill({ json: current() });
		}
		return route.fulfill({ status: 404, json: { detail: { code: 'not_found' } } });
	}

	return {
		requests,
		install: async () => {
			await page.route('/api/auth/token', (route) => route.fulfill({ json: { token } }));
			await page.route('/api/loan-options', (route) =>
				route.fulfill({
					json: {
						policy_version: '2026.1',
						khr_per_usd: '4000.00',
						max_amount: { USD: '20000', KHR: '80000000' },
						min_term_months: 3,
						max_term_months: 60,
						products: ['personal', 'small_business']
					}
				})
			);
			await page.route('/api/applications**', handle);
		}
	};
}

function signInAsCustomer(page: Page) {
	const expiresAt = new Date(Date.now() + 3_600_000).toISOString();
	return page.route('/api/auth/get-session*', (route) =>
		route.fulfill({
			json: {
				session: { id: 's1', userId: 'u1', token: 't1', expiresAt, createdAt: now, updatedAt: now },
				user: {
					id: 'u1',
					name: 'Sample Customer',
					email: 'customer@example.com',
					emailVerified: false,
					role: 'customer',
					createdAt: now,
					updatedAt: now
				}
			}
		})
	);
}

const samplePdf = (name: string) => ({
	name,
	mimeType: 'application/pdf',
	buffer: Buffer.from('%PDF-1.4\n% SAMPLE — NOT A REAL DOCUMENT\n%%EOF\n')
});

async function upload(page: Page, slot: string, file = samplePdf(`${slot}.pdf`)) {
	const chooser = page.waitForEvent('filechooser');
	await page.getByRole('button', { name: `Choose file: ${slot}` }).click();
	await (await chooser).setFiles(file);
}

test.beforeEach(async ({ page }) => {
	await page.route('/api/auth/ok', (route) => route.fulfill({ json: { ok: true } }));
	await signInAsCustomer(page);
});

test('a customer applies for a riel loan, uploads documents and submits', async ({ page }) => {
	const api = fakeApi(page);
	await api.install();

	await page.goto('/apply');
	await expect(page.getByText('Step 1 of 4')).toBeVisible();
	await page.getByRole('radio', { name: 'Riel (៛)' }).click();
	await expect(page.getByText('Up to ៛80,000,000')).toBeVisible();
	await page.getByLabel('Amount').fill('32,000,000');
	await expect(page.getByText('About $8,000.00.')).toContainText('4,000 riel per dollar');
	await page.getByLabel('Term in months').fill('24');
	await page.getByLabel('What is the loan for?').fill('Stock for a sample shop');
	await page.getByRole('button', { name: 'Save and continue' }).click();

	await expect(page).toHaveURL('/apply/app-1?step=about');
	expect(api.requests.find((r) => r.method === 'POST')?.body).toEqual({
		product: 'personal',
		currency: 'KHR',
		amount: '32000000',
		term_months: 24,
		purpose: 'Stock for a sample shop'
	});

	await page.getByLabel('Name in Latin letters').fill('Sample Customer');
	await page.getByLabel('Date of birth').fill('1990-05-01');
	await page.getByLabel('National ID number').fill('123456789');
	await page.getByLabel('Phone number').fill('012 345 678');
	await page.getByRole('button', { name: 'Save and continue' }).click();

	await expect(page).toHaveURL('/apply/app-1?step=documents');
	for (const slot of ['National ID card', 'Payslip', 'Bank statement']) {
		await upload(page, slot);
		await expect(page.getByRole('button', { name: `Replace: ${slot}` })).toBeVisible();
	}
	await expect(page.getByText('Pages: 1')).toHaveCount(3);
	await page.getByRole('button', { name: 'Save and continue' }).click();

	await expect(page).toHaveURL('/apply/app-1?step=review');
	await expect(page.getByText('៛32,000,000')).toBeVisible();
	const submit = page.getByRole('button', { name: 'Submit application' });
	await expect(submit).toBeDisabled();
	await page.getByRole('checkbox', { name: /sample documents/ }).click();
	await submit.click();

	await expect(page).toHaveURL('/my/app-1');
	await expect(page.locator('[aria-current="step"]')).toHaveText('2 Checking your documents');

	await page.getByRole('link', { name: /All applications/ }).click();
	await expect(page).toHaveURL('/my');
	const item = page.getByRole('link', { name: /៛32,000,000/ });
	await expect(item).toContainText('Checking your documents');
});

test('a refused file shows why, in the customer’s words', async ({ page }) => {
	const api = fakeApi(page, {
		refuse: 'unsupported_file_type',
		draft: {
			applicant: {
				full_name_km: null,
				full_name_en: 'Sample Customer',
				dob: '1990-05-01',
				national_id: '123456789',
				phone: '012345678'
			}
		}
	});
	await api.install();

	await page.goto('/apply/app-1');
	await expect(page).toHaveURL('/apply/app-1');
	await expect(page.getByText('Step 3 of 4')).toBeVisible();
	await upload(page, 'Payslip', { ...samplePdf('notes.pdf'), buffer: Buffer.from('just text') });

	await expect(page.getByRole('alert')).toHaveText('Only PDF, JPEG and PNG files can be uploaded.');
	await expect(page.getByRole('button', { name: 'Choose file: Payslip' })).toBeVisible();
});
