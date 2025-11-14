import { apiRequest } from './client';
import type { Item } from './items';

export interface Match {
	id: string;
	lost_item_id: string;
	found_item_id: string;
	loser_id: string;
	finder_id: string;
	confidence_score: number;
	match_status: 'PENDING' | 'APPROVED' | 'REJECTED';
	created_at: string;
	lost_item: Item;
	found_item: Item;
}

export interface ApproveMatchResponse {
	match: Match;
	message: string;
	contact_shared_with_loser: {
		name: string;
		email: string;
		contact_number: string;
	};
	contact_shared_with_finder: {
		name: string;
		email: string;
		contact_number: string;
	};
}

export async function getMyMatches(): Promise<Match[]> {
	return apiRequest<Match[]>('/matches/my_matches');
}

export async function approveMatch(matchId: string): Promise<ApproveMatchResponse> {
	return apiRequest<ApproveMatchResponse>(`/matches/${matchId}/approve`, {
		method: 'POST'
	});
}

export async function rejectMatch(matchId: string): Promise<Match> {
	return apiRequest<Match>(`/matches/${matchId}/reject`, {
		method: 'POST'
	});
}

