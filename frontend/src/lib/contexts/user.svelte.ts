import { getContext, setContext } from 'svelte';
import type { User } from '$lib/api/auth';
import { getCurrentUser, updateUser as apiUpdateUser } from '$lib/api/auth';
import { getMyMatches, type Match } from '$lib/api/matches';

const USER_CONTEXT_KEY = Symbol('user');

interface UserContextValue {
	user: User | null;
	loading: boolean;
	matches: Match[];
	matchesLoading: boolean;
	init: () => Promise<void>;
	refresh: () => Promise<void>;
	update: (data: Parameters<typeof apiUpdateUser>[0]) => Promise<User>;
	setUser: (user: User | null) => void;
	refreshMatches: () => Promise<void>;
}

export function createUserContext(): UserContextValue {
	let user = $state<User | null>(null);
	let loading = $state(false);
	let matches = $state<Match[]>([]);
	let matchesLoading = $state(false);

	async function init() {
		if (user) return;
		try {
			loading = true;
			user = await getCurrentUser();
			await refreshMatches();
		} catch (error) {
			console.error('Failed to load user:', error);
			user = null;
		} finally {
			loading = false;
		}
	}

	async function refresh() {
		try {
			loading = true;
			user = await getCurrentUser();
			await refreshMatches();
		} catch (error) {
			console.error('Failed to refresh user:', error);
		} finally {
			loading = false;
		}
	}

	async function update(data: Parameters<typeof apiUpdateUser>[0]) {
		try {
			loading = true;
			user = await apiUpdateUser(data);
			return user;
		} catch (error) {
			console.error('Failed to update user:', error);
			throw error;
		} finally {
			loading = false;
		}
	}

	async function refreshMatches() {
		if (!user) return;
		try {
			matchesLoading = true;
			const newMatches = await getMyMatches();
			const previousMatchIds = new Set(matches.map(m => m.id));
			const newMatchIds = new Set(newMatches.map(m => m.id));
			
			// Check for new matches
			const newlyCreatedMatches = newMatches.filter(m => !previousMatchIds.has(m.id));
			
			matches = newMatches;
			
			return newlyCreatedMatches;
		} catch (error) {
			console.error('Failed to refresh matches:', error);
			return [];
		} finally {
			matchesLoading = false;
		}
	}

	function setUser(newUser: User | null) {
		user = newUser;
		if (!newUser) {
			matches = [];
		}
	}

	return {
		get user() {
			return user;
		},
		get loading() {
			return loading;
		},
		get matches() {
			return matches;
		},
		get matchesLoading() {
			return matchesLoading;
		},
		init,
		refresh,
		update,
		setUser,
		refreshMatches
	};
}

export function setUserContext() {
	const context = createUserContext();
	setContext(USER_CONTEXT_KEY, context);
	return context;
}

export function getUserContext(): UserContextValue {
	return getContext<UserContextValue>(USER_CONTEXT_KEY);
}

