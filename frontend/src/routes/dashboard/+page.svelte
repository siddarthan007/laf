<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Tooltip, TooltipContent, TooltipTrigger } from '$lib/components/ui/tooltip';
	import { Search, FileQuestion, CheckCircle, Package, Info, ArrowRight, Sparkles } from "@lucide/svelte";
	import { getAllFoundItems, searchItems } from '$lib/api/items';
	import { getMyMatches } from '$lib/api/matches';
	import { getImageUrl } from '$lib/api/config';
	import { onMount } from 'svelte';
	import type { Item } from '$lib/api/items';
	import type { Match } from '$lib/api/matches';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { getUserContext } from '$lib/contexts/user.svelte';
	import { onDestroy } from 'svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { fade, fly } from 'svelte/transition';
	import { triggerMatchConfetti } from '$lib/utils/confetti';

	const userContext = getUserContext();

	let foundItems = $state<Item[]>([]);
	let matches = $state<Match[]>([]);
	let loading = $state(true);
	let pollInterval: ReturnType<typeof setInterval> | null = null;

	async function loadData() {
		try {
			const [items, userMatches] = await Promise.all([
				getAllFoundItems(),
				getMyMatches()
			]);
			// Limit to 5 for display
			foundItems = items.slice(0, 5);
			matches = userMatches;
		} catch (err) {
			console.error('Failed to load dashboard data:', err);
			toast.error('Failed to load dashboard data. Please refresh the page.');
		} finally {
			loading = false;
		}
	}

	async function checkForNewMatches() {
		if (!userContext.user) return;
		try {
			const previousMatchIds = new Set(matches.map(m => m.id));
			const previousMatchStatuses = new Map(matches.map(m => [m.id, m.match_status]));
			const newMatches = await getMyMatches();
			
			// Check if there are actual changes
			const hasNewMatches = newMatches.some(m => !previousMatchIds.has(m.id));
			const hasStatusChanges = newMatches.some(m => {
				const prevStatus = previousMatchStatuses.get(m.id);
				return prevStatus !== undefined && prevStatus !== m.match_status;
			});
			
			// Only update if there are actual changes
			if (hasNewMatches || hasStatusChanges) {
				// Find newly created matches for toast notification
				const newlyCreatedMatches = newMatches.filter(m => !previousMatchIds.has(m.id));
				
				if (newlyCreatedMatches.length > 0) {
					matches = newMatches;
					triggerMatchConfetti();
					toast.info(`New match${newlyCreatedMatches.length !== 1 ? 'es' : ''} found!`, {
						description: `${newlyCreatedMatches.length} potential match${newlyCreatedMatches.length !== 1 ? 'es' : ''} ${newlyCreatedMatches.length !== 1 ? 'are' : 'is'} waiting for your review.`,
						duration: 5000
					});
				} else {
					// Update matches silently if only status changed
					matches = newMatches;
				}
			}
		} catch (err) {
			console.error('Failed to check for new matches:', err);
		}
	}

	onMount(async () => {
		// Redirect admins to admin dashboard
		if (authStore.isAdmin) {
			await goto('/dashboard/admin');
			return;
		}
		
		await loadData();
		
		// Poll for new matches every 30 seconds (reduced frequency to avoid visible refreshes)
		pollInterval = setInterval(() => {
			checkForNewMatches();
		}, 30000);
	});

	onDestroy(() => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}
	});

	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<div class="space-y-8 pb-12">
	<!-- Welcome Section -->
	<div class="relative overflow-hidden rounded-3xl glass p-8 sm:p-12" in:fade={{ duration: 500 }}>
		<div class="relative z-10 max-w-2xl">
			<h1 class="text-4xl sm:text-5xl font-bold tracking-tight mb-4 bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600">
				Welcome back, {userContext.user?.name?.split(' ')[0] || 'User'}!
			</h1>
			<p class="text-lg text-muted-foreground mb-8 leading-relaxed">
				Here's what's happening with your lost and found items. We're constantly scanning for matches to help you recover what's yours.
			</p>
			<div class="flex flex-wrap gap-4">
				<Button size="lg" class="rounded-full px-8 shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all hover:-translate-y-0.5" onclick={() => goto('/dashboard/report')}>
					<FileQuestion class="mr-2 h-5 w-5" />
					Report Lost Item
				</Button>
				<Button variant="outline" size="lg" class="rounded-full px-8 border-primary/20 hover:bg-primary/5" onclick={() => goto('/dashboard/found')}>
					<Search class="mr-2 h-5 w-5" />
					Browse Found
				</Button>
			</div>
		</div>
		
		<!-- Decorative Background Elements -->
		<div class="absolute top-0 right-0 -mt-20 -mr-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl"></div>
		<div class="absolute bottom-0 right-20 -mb-20 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl"></div>
	</div>

	<!-- Stats Grid -->
	<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
		<div class="card-premium group cursor-pointer" onclick={() => goto('/dashboard/found')}>
			<div class="flex justify-between items-start mb-4">
				<div class="p-3 rounded-2xl bg-blue-500/10 text-blue-600 group-hover:bg-blue-500/20 transition-colors">
					<Package class="h-6 w-6" />
				</div>
				<Badge variant="outline" class="bg-white/50 backdrop-blur-sm">Live</Badge>
			</div>
			<div class="space-y-1">
				<h3 class="text-3xl font-bold tracking-tight">
					{#if loading}<Skeleton class="h-8 w-16 inline-block" />{:else}{foundItems.length}{/if}
				</h3>
				<p class="text-sm text-muted-foreground font-medium">Found Items</p>
			</div>
		</div>

		<div class="card-premium group cursor-pointer" onclick={() => goto('/dashboard/matches')}>
			<div class="flex justify-between items-start mb-4">
				<div class="p-3 rounded-2xl bg-amber-500/10 text-amber-600 group-hover:bg-amber-500/20 transition-colors">
					<Sparkles class="h-6 w-6" />
				</div>
				{#if !loading && matches.filter((m) => m.match_status === 'PENDING').length > 0}
					<span class="relative flex h-3 w-3">
					  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
					  <span class="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
					</span>
				{/if}
			</div>
			<div class="space-y-1">
				<h3 class="text-3xl font-bold tracking-tight">
					{#if loading}<Skeleton class="h-8 w-16 inline-block" />{:else}{matches.filter((m) => m.match_status === 'PENDING').length}{/if}
				</h3>
				<p class="text-sm text-muted-foreground font-medium">Pending Matches</p>
			</div>
		</div>

		<div class="card-premium group cursor-pointer" onclick={() => goto('/dashboard/matches')}>
			<div class="flex justify-between items-start mb-4">
				<div class="p-3 rounded-2xl bg-green-500/10 text-green-600 group-hover:bg-green-500/20 transition-colors">
					<CheckCircle class="h-6 w-6" />
				</div>
			</div>
			<div class="space-y-1">
				<h3 class="text-3xl font-bold tracking-tight">
					{#if loading}<Skeleton class="h-8 w-16 inline-block" />{:else}{matches.filter((m) => m.match_status === 'APPROVED').length}{/if}
				</h3>
				<p class="text-sm text-muted-foreground font-medium">Approved Matches</p>
			</div>
		</div>

		<div class="card-premium group cursor-pointer" onclick={() => goto('/dashboard/my-items')}>
			<div class="flex justify-between items-start mb-4">
				<div class="p-3 rounded-2xl bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
					<FileQuestion class="h-6 w-6" />
				</div>
			</div>
			<div class="space-y-1">
				<h3 class="text-3xl font-bold tracking-tight">
					{#if loading}<Skeleton class="h-8 w-16 inline-block" />{:else}0{/if}
				</h3>
				<p class="text-sm text-muted-foreground font-medium">My Reports</p>
			</div>
		</div>
	</div>

	<div class="grid gap-8 grid-cols-1 lg:grid-cols-2">
		<!-- Recent Found Items -->
		<div class="space-y-6">
			<div class="flex items-center justify-between">
				<h2 class="text-2xl font-bold tracking-tight">Recent Found Items</h2>
				<Button variant="ghost" class="text-primary hover:text-primary/80 hover:bg-primary/5" onclick={() => goto('/dashboard/found')}>
					View All <ArrowRight class="ml-2 h-4 w-4" />
				</Button>
			</div>
			
			<div class="space-y-4">
				{#if loading}
					{#each Array(3) as _}
						<div class="glass rounded-2xl p-4 flex gap-4">
							<Skeleton class="w-20 h-20 rounded-xl" />
							<div class="flex-1 space-y-2 py-1">
								<Skeleton class="h-5 w-3/4" />
								<Skeleton class="h-4 w-1/2" />
							</div>
						</div>
					{/each}
				{:else if foundItems.length === 0}
					<div class="glass rounded-3xl p-12 text-center">
						<div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted mb-4">
							<Package class="h-8 w-8 text-muted-foreground" />
						</div>
						<h3 class="text-lg font-semibold">No items found yet</h3>
						<p class="text-muted-foreground mt-1">Check back later for updates</p>
					</div>
				{:else}
					{#each foundItems as item, i}
						<div 
							class="glass glass-hover rounded-2xl p-3 flex gap-4 cursor-pointer group"
							in:fly={{ y: 20, delay: i * 50, duration: 400 }}
							onclick={() => goto(`/dashboard/found`)}
						>
							<div class="w-20 h-20 rounded-xl overflow-hidden bg-muted flex-shrink-0 border border-white/10">
								{#if item.image_url}
									<img
										src={getImageUrl(item.image_url)}
										alt={item.description}
										class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
									/>
								{:else}
									<div class="w-full h-full flex items-center justify-center">
										<Package class="h-8 w-8 text-muted-foreground/50" />
									</div>
								{/if}
							</div>
							<div class="flex-1 py-1 min-w-0">
								<div class="flex items-start justify-between gap-2">
									<h3 class="font-semibold truncate pr-2 group-hover:text-primary transition-colors">{item.description}</h3>
									<Badge variant="secondary" class="bg-white/50 backdrop-blur-sm text-xs">{item.status}</Badge>
								</div>
								<p class="text-sm text-muted-foreground mt-1 truncate">{item.location}</p>
								<p class="text-xs text-muted-foreground/70 mt-2">{formatDate(item.reported_at)}</p>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Pending Matches -->
		<div class="space-y-6">
			<div class="flex items-center justify-between">
				<h2 class="text-2xl font-bold tracking-tight">Potential Matches</h2>
				<Button variant="ghost" class="text-primary hover:text-primary/80 hover:bg-primary/5" onclick={() => goto('/dashboard/matches')}>
					View All <ArrowRight class="ml-2 h-4 w-4" />
				</Button>
			</div>

			<div class="space-y-4">
				{#if loading}
					{#each Array(2) as _}
						<div class="glass rounded-2xl p-6 space-y-4">
							<Skeleton class="h-5 w-full" />
							<Skeleton class="h-4 w-3/4" />
						</div>
					{/each}
				{:else if matches.filter((m) => m.match_status === 'PENDING').length === 0}
					<div class="glass rounded-3xl p-12 text-center">
						<div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted mb-4">
							<CheckCircle class="h-8 w-8 text-muted-foreground" />
						</div>
						<h3 class="text-lg font-semibold">All caught up!</h3>
						<p class="text-muted-foreground mt-1">We'll notify you when we find a match</p>
					</div>
				{:else}
					{#each matches.filter((m) => m.match_status === 'PENDING') as match, i}
						<div 
							class="glass glass-hover rounded-2xl p-5 cursor-pointer group relative overflow-hidden"
							in:fly={{ y: 20, delay: i * 50, duration: 400 }}
							onclick={() => goto('/dashboard/matches')}
						>
							<div class="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
							
							<div class="flex items-start justify-between gap-4 mb-3">
								<div>
									<h3 class="font-semibold text-lg group-hover:text-primary transition-colors">Match Found</h3>
									<p class="text-sm text-muted-foreground">Confidence Score</p>
								</div>
								<div class="flex items-center gap-1 bg-primary/10 text-primary px-3 py-1 rounded-full font-bold text-sm">
									<Sparkles class="w-3 h-3" />
									{(match.confidence_score * 100).toFixed(0)}%
								</div>
							</div>
							
							<div class="grid grid-cols-2 gap-4 text-sm">
								<div class="p-3 rounded-xl bg-muted/50">
									<p class="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Lost Item</p>
									<p class="font-medium truncate">{match.lost_item.description}</p>
								</div>
								<div class="p-3 rounded-xl bg-muted/50">
									<p class="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Found Item</p>
									<p class="font-medium truncate">{match.found_item.description}</p>
								</div>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	</div>
</div>
