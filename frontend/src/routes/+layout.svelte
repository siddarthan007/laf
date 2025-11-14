<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Toaster } from '$lib/components/ui/sonner';
	import { TooltipProvider } from '$lib/components/ui/tooltip';

	let { children } = $props();

	onMount(async () => {
		await authStore.init();
	});

	$effect(() => {
		if (!authStore.initialized) return;
		const isAuthPage = $page.url.pathname === '/login' || $page.url.pathname === '/register';
		if (!authStore.isAuthenticated && !isAuthPage) {
			goto('/login');
		} else if (authStore.isAuthenticated && isAuthPage) {
			goto(authStore.isAdmin ? '/dashboard/admin' : '/dashboard');
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Findora</title>
</svelte:head>

<TooltipProvider>
	<Toaster />
	{@render children()}
</TooltipProvider>
