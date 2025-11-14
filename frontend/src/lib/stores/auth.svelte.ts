import type { User } from '$lib/api/auth';
import { getCurrentUser, isAuthenticated, logout as apiLogout } from '$lib/api/auth';
import { goto } from '$app/navigation';

class AuthStore {
	user = $state<User | null>(null);
	loading = $state(false);
	initialized = $state(false);

	async init() {
		if (this.initialized) return;
		this.initialized = true;

		if (isAuthenticated()) {
			try {
				this.loading = true;
				this.user = await getCurrentUser();
			} catch {
				apiLogout();
				this.user = null;
			} finally {
				this.loading = false;
			}
		}
	}

	async setUser(user: User) {
		this.user = user;
	}

	async logout() {
		apiLogout();
		this.user = null;
		await goto('/login');
	}

	get isAuthenticated() {
		return !!this.user;
	}

	get isAdmin() {
		return this.user?.role === 'ADMIN';
	}
}

export const authStore = new AuthStore();

