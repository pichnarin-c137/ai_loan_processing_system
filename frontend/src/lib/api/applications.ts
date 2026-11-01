import { queryOptions, type QueryClient } from '@tanstack/svelte-query';
import { api, authedFetch } from './client.js';
import { ApiError } from './errors.js';
import type { components } from './schema.js';

export type ApplicationDetail = components['schemas']['ApplicationDetail'];
export type ApplicationSummary = components['schemas']['ApplicationSummary'];
export type LoanOptions = components['schemas']['LoanOptions'];
export type LoanIn = components['schemas']['LoanIn'];
export type ApplicantIn = components['schemas']['ApplicantIn'];
export type DocumentOut = components['schemas']['DocumentOut'];
export type DocType = components['schemas']['DocType'];
export type Product = components['schemas']['Product'];

/** Returns the data, or throws an ApiError carrying the error body. */
async function unwrap<T>(
	request: Promise<{ data?: T; error?: unknown; response: Response }>
): Promise<T> {
	const { data, error, response } = await request;
	if (!response.ok || data === undefined) throw new ApiError(response.status, error);
	return data;
}

export const applicationKeys = {
	all: ['applications'] as const,
	detail: (id: string) => ['applications', id] as const,
	loanOptions: ['loan-options'] as const
};

export const loanOptionsQuery = () =>
	queryOptions({
		queryKey: applicationKeys.loanOptions,
		queryFn: () => unwrap(api.GET('/api/loan-options')),
		// The limits and rate only change with a new policy version.
		staleTime: 60 * 60 * 1000
	});

export const applicationsQuery = () =>
	queryOptions({
		queryKey: applicationKeys.all,
		queryFn: () => unwrap(api.GET('/api/applications'))
	});

export const applicationQuery = (id: string) =>
	queryOptions({
		queryKey: applicationKeys.detail(id),
		queryFn: () =>
			unwrap(api.GET('/api/applications/{app_id}', { params: { path: { app_id: id } } }))
	});

/** Puts a fresh copy of the application in the cache, and marks the list as out of date. */
export function storeApplication(client: QueryClient, detail: ApplicationDetail): void {
	client.setQueryData(applicationKeys.detail(detail.id), detail);
	void client.invalidateQueries({ queryKey: applicationKeys.all, exact: true });
}

export const createApplication = (body: LoanIn) => unwrap(api.POST('/api/applications', { body }));

export const saveLoan = (id: string, body: LoanIn) =>
	unwrap(api.PUT('/api/applications/{app_id}/loan', { params: { path: { app_id: id } }, body }));

export const saveApplicant = (id: string, body: ApplicantIn) =>
	unwrap(
		api.PUT('/api/applications/{app_id}/applicant', { params: { path: { app_id: id } }, body })
	);

export const submitApplication = (id: string) =>
	unwrap(
		api.POST('/api/applications/{app_id}/submit', {
			params: { path: { app_id: id } },
			body: { confirm_sample: true }
		})
	);

/**
 * Sends the file itself as the request body. The API decides the type from the file's first
 * bytes, so Content-Type is only a hint.
 */
export async function uploadDocument(
	id: string,
	docType: DocType,
	file: Blob
): Promise<DocumentOut> {
	const url = `/api/applications/${encodeURIComponent(id)}/documents/${docType}`;
	const response = await authedFetch(
		new Request(url, {
			method: 'PUT',
			body: file,
			headers: { 'Content-Type': file.type || 'application/octet-stream' }
		})
	);
	const body: unknown = await response.json().catch(() => null);
	if (!response.ok) throw new ApiError(response.status, body);
	return body as DocumentOut;
}
