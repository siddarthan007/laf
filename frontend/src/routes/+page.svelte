<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth.svelte';

	onMount(async () => {
		await authStore.init();
		if (authStore.isAuthenticated) {
			goto(authStore.isAdmin ? '/dashboard/admin' : '/dashboard');
		} else {
			goto('/login');
		}
	});
</script>

<div class="min-h-screen flex items-center justify-center">
	<div class="text-center">
		<h1 class="text-2xl font-bold">Loading...</h1>
	</div>
</div>
