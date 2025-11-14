import { apiRequest } from './client';
import type { Item } from './items';
import type { Match } from './matches';
import type { User } from './auth';

export interface ReportOnBehalfRequest {
	user_identifier: string;
	item_status: 'LOST' | 'FOUND';
	description: string;
	location: string;
	image?: File;
}

export interface ReportOfficeItemRequest {
	item_status: 'FOUND';
	description: string;
	location: string;
	image: File;
}

export interface Analytics {
	totals: {
		users: number;
		lost_active: number;
		found_active: number;
		resolved: number;
		matches_pending: number;
		matches_approved: number;
	};
	daily_reports_last_30_days: Record<string, { LOST: number; FOUND: number }>;
}

export interface ItemsListParams {
	limit?: number;
	offset?: number;
	status?: 'LOST' | 'FOUND';
	include_archived?: boolean;
	q?: string;
	include_matches?: boolean;
}

export interface MatchesListParams {
	limit?: number;
	offset?: number;
	status?: 'PENDING' | 'APPROVED' | 'REJECTED';
}

export interface UsersListParams {
	limit?: number;
	offset?: number;
}

export async function reportOnBehalf(data: ReportOnBehalfRequest): Promise<Item> {
	const formData = new FormData();
	formData.append('user_identifier', data.user_identifier);
	formData.append('item_status', data.item_status);
	formData.append('description', data.description);
	formData.append('location', data.location);
	if (data.image) {
		formData.append('image', data.image);
	}

	return apiRequest<Item>('/admin/report_on_behalf', {
		method: 'POST',
		body: formData
	});
}

export async function reportOfficeItem(data: ReportOfficeItemRequest): Promise<Item> {
	const formData = new FormData();
	formData.append('item_status', data.item_status);
	formData.append('description', data.description);
	formData.append('location', data.location);
	formData.append('image', data.image);

	return apiRequest<Item>('/admin/report_office_item', {
		method: 'POST',
		body: formData
	});
}

export async function getAnalytics(): Promise<Analytics> {
	return apiRequest<Analytics>('/admin/dashboard/analytics');
}

export async function getUsers(params?: UsersListParams): Promise<User[]> {
	const query = new URLSearchParams();
	if (params?.limit) query.append('limit', params.limit.toString());
	if (params?.offset) query.append('offset', params.offset.toString());

	return apiRequest<User[]>(`/admin/dashboard/users${query.toString() ? `?${query.toString()}` : ''}`);
}

export async function getItems(params?: ItemsListParams): Promise<Item[]> {
	const query = new URLSearchParams();
	if (params?.limit) query.append('limit', params.limit.toString());
	if (params?.offset) query.append('offset', params.offset.toString());
	if (params?.status) query.append('status', params.status);
	if (params?.include_archived !== undefined) query.append('include_archived', params.include_archived.toString());
	if (params?.q) query.append('q', params.q);
	if (params?.include_matches !== undefined) query.append('include_matches', params.include_matches.toString());

	return apiRequest<Item[]>(`/admin/dashboard/items${query.toString() ? `?${query.toString()}` : ''}`);
}

export async function getMatches(params?: MatchesListParams): Promise<Match[]> {
	const query = new URLSearchParams();
	if (params?.limit) query.append('limit', params.limit.toString());
	if (params?.offset) query.append('offset', params.offset.toString());
	if (params?.status) query.append('status', params.status);

	return apiRequest<Match[]>(`/admin/dashboard/matches${query.toString() ? `?${query.toString()}` : ''}`);
}

