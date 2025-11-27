<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth.svelte';
	import { Button } from '$lib/components/ui/button';
	import { ArrowRight, Search, Shield, Zap, Sparkles, CheckCircle } from 'lucide-svelte';
	import { fade, fly } from 'svelte/transition';

	let mounted = $state(false);

	onMount(async () => {
		await authStore.init();
		if (authStore.isAuthenticated) {
			goto(authStore.isAdmin ? '/dashboard/admin' : '/dashboard');
		}
		mounted = true;
	});
</script>

<div class="min-h-screen flex flex-col relative overflow-hidden bg-background selection:bg-primary/20 selection:text-primary">
	<!-- Animated Background -->
	<div class="absolute inset-0 -z-10 overflow-hidden">
		<div class="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[100px] animate-pulse duration-[10s]"></div>
		<div class="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[120px] animate-pulse duration-[15s]"></div>
	</div>

	<!-- Navbar -->
	<nav class="container mx-auto px-6 py-6 flex items-center justify-between relative z-10">
		<div class="flex items-center gap-2">
			<div class="bg-primary/10 p-2 rounded-xl">
				<Sparkles class="h-6 w-6 text-primary" />
			</div>
			<span class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600 tracking-tight">Findora</span>
		</div>
		<div class="flex items-center gap-4">
			<a href="/login" class="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Log in</a>
			<Button onclick={() => goto('/register')} class="rounded-full px-6 shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all hover:-translate-y-0.5">
				Get Started
			</Button>
		</div>
	</nav>

	<!-- Hero Section -->
	<main class="flex-1 container mx-auto px-6 flex flex-col items-center justify-center text-center relative z-10 py-20">
		{#if mounted}
			<div in:fly={{ y: 20, duration: 800, delay: 200 }} class="space-y-8 max-w-4xl mx-auto">
				<div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/5 border border-primary/10 text-primary text-sm font-medium mb-4">
					<span class="relative flex h-2 w-2">
					  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
					  <span class="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
					</span>
					AI-Powered Lost & Found
				</div>
				
				<h1 class="text-5xl md:text-7xl font-bold tracking-tight leading-tight">
					Reuniting you with <br />
					<span class="bg-clip-text text-transparent bg-gradient-to-r from-primary via-purple-500 to-pink-500 animate-gradient">what matters most.</span>
				</h1>
				
				<p class="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
					Findora uses advanced AI matching to instantly connect lost items with found reports. 
					Simple, fast, and secure.
				</p>
				
				<div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
					<Button size="lg" class="rounded-full px-8 h-14 text-lg shadow-xl shadow-primary/25 hover:shadow-primary/40 transition-all hover:-translate-y-1" onclick={() => goto('/register')}>
						Report an Item <ArrowRight class="ml-2 h-5 w-5" />
					</Button>
					<Button variant="outline" size="lg" class="rounded-full px-8 h-14 text-lg border-primary/20 hover:bg-primary/5 backdrop-blur-sm" onclick={() => goto('/login')}>
						Browse Found Items
					</Button>
				</div>
			</div>

			<!-- Features Grid -->
			<div in:fly={{ y: 40, duration: 800, delay: 400 }} class="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 w-full max-w-6xl">
				<div class="glass p-8 rounded-3xl hover:bg-card/80 transition-all duration-300 hover:-translate-y-1 group">
					<div class="w-14 h-14 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
						<Zap class="h-7 w-7 text-blue-600" />
					</div>
					<h3 class="text-xl font-bold mb-3">Instant Matching</h3>
					<p class="text-muted-foreground leading-relaxed">Our AI algorithms analyze descriptions and images to find matches in seconds, not days.</p>
				</div>
				
				<div class="glass p-8 rounded-3xl hover:bg-card/80 transition-all duration-300 hover:-translate-y-1 group">
					<div class="w-14 h-14 rounded-2xl bg-purple-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
						<Search class="h-7 w-7 text-purple-600" />
					</div>
					<h3 class="text-xl font-bold mb-3">Smart Search</h3>
					<p class="text-muted-foreground leading-relaxed">Search through found items with semantic understanding. "Blue bag" finds "Navy backpack".</p>
				</div>
				
				<div class="glass p-8 rounded-3xl hover:bg-card/80 transition-all duration-300 hover:-translate-y-1 group">
					<div class="w-14 h-14 rounded-2xl bg-green-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
						<Shield class="h-7 w-7 text-green-600" />
					</div>
					<h3 class="text-xl font-bold mb-3">Secure & Verified</h3>
					<p class="text-muted-foreground leading-relaxed">Your data is safe. We verify matches before connecting you with the finder.</p>
				</div>
			</div>
		{/if}
	</main>

	<!-- Footer -->
	<footer class="container mx-auto px-6 py-8 text-center text-muted-foreground text-sm relative z-10">
		<p>&copy; {new Date().getFullYear()} Findora. All rights reserved.</p>
	</footer>
</div>

<style>
	.animate-gradient {
		background-size: 200% 200%;
		animation: gradient 8s ease infinite;
	}
	
	@keyframes gradient {
		0% { background-position: 0% 50%; }
		50% { background-position: 100% 50%; }
		100% { background-position: 0% 50%; }
	}
</style>
