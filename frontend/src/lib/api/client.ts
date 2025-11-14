import { API_BASE_URL } from './config';

const API_BASE = API_BASE_URL;

export interface ApiError {
	detail: string | Array<{ loc: string[]; msg: string; type: string }>;
}

export class ApiClientError extends Error {
	constructor(
		public status: number,
		public error: ApiError
	) {
		super(typeof error.detail === 'string' ? error.detail : 'API Error');
		this.name = 'ApiClientError';
	}
}

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const error: ApiError = await response.json().catch(() => ({
			detail: `HTTP ${response.status}: ${response.statusText}`
		}));
		throw new ApiClientError(response.status, error);
	}
	return response.json();
}

export async function apiRequest<T>(
	endpoint: string,
	options: RequestInit = {}
): Promise<T> {
	const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

	const headers: Record<string, string> = {
		...(options.headers as Record<string, string>)
	};

	// Don't set Content-Type for FormData
	if (!(options.body instanceof FormData)) {
		headers['Content-Type'] = 'application/json';
	}

	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}

	const response = await fetch(`${API_BASE}${endpoint}`, {
		...options,
		headers
	});

	// Handle token refresh on 401
	if (response.status === 401 && typeof window !== 'undefined') {
		const refreshToken = localStorage.getItem('refresh_token');
		if (refreshToken) {
			try {
				const refreshed = await refreshTokenRequest(refreshToken);
				if (refreshed) {
					// Retry original request
					const retryHeaders: Record<string, string> = {
						...headers,
						'Authorization': `Bearer ${refreshed.access_token}`
					};
					const retryResponse = await fetch(`${API_BASE}${endpoint}`, {
						...options,
						headers: retryHeaders
					});
					return handleResponse<T>(retryResponse);
				}
			} catch {
				// Refresh failed, clear tokens
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
				// Redirect will be handled by auth store
			}
		}
	}

	return handleResponse<T>(response);
}

async function refreshTokenRequest(refreshToken: string): Promise<{ access_token: string; refresh_token: string } | null> {
	try {
		const response = await fetch(`${API_BASE}/auth/refresh`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ refresh_token: refreshToken })
		});

		if (!response.ok) {
			return null;
		}

		const data = await response.json();
		if (typeof window !== 'undefined') {
			localStorage.setItem('access_token', data.access_token);
			localStorage.setItem('refresh_token', data.refresh_token);
		}
		return data;
	} catch {
		return null;
	}
}

