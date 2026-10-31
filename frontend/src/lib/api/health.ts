export type ServiceName = 'api' | 'database' | 'redis' | 'storage' | 'auth';

export interface ServiceStatus {
	name: ServiceName;
	ok: boolean;
}

/** Body of GET /api/health (backend/app/api/health.py). */
export interface HealthReport {
	status: 'ok' | 'degraded';
	checks: Record<'database' | 'redis' | 'storage', boolean>;
}

const backendChecks = ['database', 'redis', 'storage'] as const;

/** One row per service. If the API did not answer, the services behind it count as down too. */
export function toServiceStatuses(report: HealthReport | null, authOk: boolean): ServiceStatus[] {
	return [
		{ name: 'api', ok: report !== null },
		...backendChecks.map((name) => ({ name, ok: report?.checks[name] === true })),
		{ name: 'auth', ok: authOk }
	];
}

function isHealthReport(value: unknown): value is HealthReport {
	return (
		typeof value === 'object' &&
		value !== null &&
		'checks' in value &&
		typeof value.checks === 'object' &&
		value.checks !== null
	);
}

/** The parsed JSON body, or null if the request or parsing failed or took longer than 5 seconds. */
async function getJson(fetchFn: typeof fetch, url: string): Promise<unknown> {
	try {
		const response = await fetchFn(url, { signal: AbortSignal.timeout(5000) });
		return (await response.json()) as unknown;
	} catch {
		return null;
	}
}

/** Never throws: an unreachable service is reported as down. */
export async function fetchHealth(fetchFn: typeof fetch = fetch): Promise<ServiceStatus[]> {
	// /api/health answers 503 with the same body when a check fails, so read the body either way.
	const [health, auth] = await Promise.all([
		getJson(fetchFn, '/api/health'),
		getJson(fetchFn, '/api/auth/ok')
	]);
	const authOk = typeof auth === 'object' && auth !== null && 'ok' in auth && auth.ok === true;
	return toServiceStatuses(isHealthReport(health) ? health : null, authOk);
}
