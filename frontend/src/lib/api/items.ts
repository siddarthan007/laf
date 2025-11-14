import { apiRequest } from './client';

export interface Item {
	id: string;
	status: 'LOST' | 'FOUND';
	description: string;
	location: string;
	image_url?: string;
	is_active: boolean;
	is_admin_report: boolean;
	has_match_found: boolean;
	reported_at: string;
	reported_by: {
		id: string;
		name: string;
		email: string;
		contact_number: string;
	};
	similarity_score?: number | null;
}

export interface ReportItemRequest {
	description: string;
	location: string;
	image?: File;
}

export async function reportLostItem(data: ReportItemRequest): Promise<Item> {
	const formData = new FormData();
	formData.append('description', data.description);
	formData.append('location', data.location);
	if (data.image) {
		formData.append('image', data.image);
	}

	return apiRequest<Item>('/items/report_lost', {
		method: 'POST',
		body: formData
	});
}

export async function reportFoundItem(data: ReportItemRequest & { image: File }): Promise<Item> {
	const formData = new FormData();
	formData.append('description', data.description);
	formData.append('location', data.location);
	formData.append('image', data.image);

	return apiRequest<Item>('/items/report_found', {
		method: 'POST',
		body: formData
	});
}

export interface FoundItemsFilters {
	location?: string;
	date_after?: string;
	date_before?: string;
	limit?: number;
}

export async function getAllFoundItems(filters?: FoundItemsFilters): Promise<Item[]> {
	const params = new URLSearchParams();
	if (filters?.location) params.append('location', filters.location);
	if (filters?.date_after) params.append('date_after', filters.date_after);
	if (filters?.date_before) params.append('date_before', filters.date_before);

	const query = params.toString();
	return apiRequest<Item[]>(`/items/all_found_items${query ? `?${query}` : ''}`);
}

export interface SearchItemsParams {
	q: string;
	status?: 'LOST' | 'FOUND';
}

export async function searchItems(params: SearchItemsParams): Promise<Item[]> {
	const query = new URLSearchParams({ q: params.q });
	if (params.status) query.append('status', params.status);

	return apiRequest<Item[]>(`/items/search?${query.toString()}`);
}

export async function resolveItem(itemId: string): Promise<Item> {
	return apiRequest<Item>(`/items/${itemId}/resolve`, {
		method: 'POST'
	});
}

export interface MyItemsFilters {
	status?: 'LOST' | 'FOUND';
	include_archived?: boolean;
}

export async function getMyItems(filters?: MyItemsFilters): Promise<Item[]> {
	const params = new URLSearchParams();
	if (filters?.status) params.append('status', filters.status);
	if (filters?.include_archived) params.append('include_archived', 'true');

	const query = params.toString();
	return apiRequest<Item[]>(`/items/my_items${query ? `?${query}` : ''}`);
}

export async function deleteItem(itemId: string): Promise<{ message: string }> {
	return apiRequest<{ message: string }>(`/items/${itemId}`, {
		method: 'DELETE'
	});
}

