import { apiRequest } from './client';
import { API_BASE_URL } from './config';

const API_BASE = API_BASE_URL;

export interface LoginRequest {
	email: string;
	password: string;
}

export interface RegisterRequest {
	name: string;
	email: string;
	password: string;
	roll_number: string;
	hostel?: string;
	contact_number: string;
}

export interface TokenResponse {
	access_token: string;
	refresh_token: string;
	token_type: string;
}

export interface User {
	id: string;
	name: string;
	email: string;
	roll_number: string;
	hostel?: string;
	contact_number: string;
	role: 'USER' | 'ADMIN';
	created_at: string;
}

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
	const response = await fetch(`${API_BASE}/auth/login`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(credentials)
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(typeof error.detail === 'string' ? error.detail : 'Login failed');
	}

	const data = await response.json();
	if (typeof window !== 'undefined') {
		localStorage.setItem('access_token', data.access_token);
		localStorage.setItem('refresh_token', data.refresh_token);
	}
	return data;
}

export async function register(data: RegisterRequest): Promise<User> {
	const response = await fetch(`${API_BASE}/auth/register`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(typeof error.detail === 'string' ? error.detail : 'Registration failed');
	}

	return response.json();
}

export async function getCurrentUser(): Promise<User> {
	return apiRequest<User>('/users/me');
}

export interface UserUpdateRequest {
	name?: string;
	email?: string;
	hostel?: string;
	contact_number?: string;
	password?: string;
}

export async function updateUser(data: UserUpdateRequest): Promise<User> {
	return apiRequest<User>('/users/me', {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});
}

export function logout(): void {
	if (typeof window !== 'undefined') {
		localStorage.removeItem('access_token');
		localStorage.removeItem('refresh_token');
	}
}

export function isAuthenticated(): boolean {
	if (typeof window === 'undefined') return false;
	return !!localStorage.getItem('access_token');
}

