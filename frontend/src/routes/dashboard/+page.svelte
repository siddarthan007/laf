<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Tooltip, TooltipContent, TooltipTrigger } from '$lib/components/ui/tooltip';
	import { Search, FileQuestion, CheckCircle, Package, Info } from "@lucide/svelte";
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

<div class="space-y-4 sm:space-y-6 md:space-y-8">
	<div class="space-y-1 sm:space-y-2">
		<h1 class="text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight">Dashboard</h1>
		<p class="text-muted-foreground text-sm sm:text-base md:text-lg">Welcome back! Here's what's happening.</p>
	</div>

	<div class="grid gap-3 sm:gap-4 md:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
		<Card class="hover:shadow-lg transition-shadow duration-200">
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-sm font-medium flex items-center gap-2">
					Found Items
					<Tooltip>
						<TooltipTrigger>
							<Info class="h-3 w-3 text-muted-foreground hover:text-foreground transition-colors" />
						</TooltipTrigger>
						<TooltipContent>
							<p>Recently found items available for matching</p>
						</TooltipContent>
					</Tooltip>
				</CardTitle>
				<Package class="h-5 w-5 text-primary" />
			</CardHeader>
			<CardContent>
				{#if loading}
					<Skeleton class="h-8 w-16 mb-2" />
				{:else}
					<div class="text-3xl font-bold">{foundItems.length}</div>
				{/if}
				<p class="text-sm text-muted-foreground mt-1">Recently found items</p>
			</CardContent>
		</Card>

		<Card class="hover:shadow-lg transition-shadow duration-200">
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-sm font-medium flex items-center gap-2">
					Pending Matches
					<Tooltip>
						<TooltipTrigger>
							<Info class="h-3 w-3 text-muted-foreground hover:text-foreground transition-colors" />
						</TooltipTrigger>
						<TooltipContent>
							<p>Matches waiting for your approval</p>
						</TooltipContent>
					</Tooltip>
				</CardTitle>
				<CheckCircle class="h-5 w-5 text-amber-500" />
			</CardHeader>
			<CardContent>
				{#if loading}
					<Skeleton class="h-8 w-16 mb-2" />
				{:else}
					<div class="text-3xl font-bold">{matches.filter((m) => m.match_status === 'PENDING').length}</div>
				{/if}
				<p class="text-sm text-muted-foreground mt-1">Awaiting your review</p>
			</CardContent>
		</Card>

		<Card class="hover:shadow-lg transition-shadow duration-200">
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-sm font-medium flex items-center gap-2">
					Approved Matches
					<Tooltip>
						<TooltipTrigger>
							<Info class="h-3 w-3 text-muted-foreground hover:text-foreground transition-colors" />
						</TooltipTrigger>
						<TooltipContent>
							<p>Successfully matched items</p>
						</TooltipContent>
					</Tooltip>
				</CardTitle>
				<CheckCircle class="h-5 w-5 text-green-500" />
			</CardHeader>
			<CardContent>
				{#if loading}
					<Skeleton class="h-8 w-16 mb-2" />
				{:else}
					<div class="text-3xl font-bold">
						{matches.filter((m) => m.match_status === 'APPROVED').length}
					</div>
				{/if}
				<p class="text-sm text-muted-foreground mt-1">Successfully matched</p>
			</CardContent>
		</Card>

		<Card class="hover:shadow-lg transition-shadow duration-200">
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-sm font-medium">Quick Actions</CardTitle>
				<FileQuestion class="h-5 w-5 text-primary" />
			</CardHeader>
			<CardContent>
				<Button class="w-full" onclick={() => goto('/dashboard/report')}>
					Report Item
				</Button>
			</CardContent>
		</Card>
	</div>

	<div class="grid gap-4 sm:gap-5 md:gap-6 grid-cols-1 lg:grid-cols-2">
		<Card class="hover:shadow-lg transition-shadow duration-200">
			<CardHeader>
				<CardTitle class="text-xl">Recent Found Items</CardTitle>
				<CardDescription class="text-base">Latest items reported as found</CardDescription>
			</CardHeader>
			<CardContent>
				{#if loading}
					<div class="space-y-4">
						{#each Array(3) as _}
							<div class="flex items-start gap-4 p-4">
								<Skeleton class="w-16 h-16 rounded-md" />
								<div class="flex-1 space-y-2">
									<Skeleton class="h-4 w-3/4" />
									<Skeleton class="h-3 w-1/2" />
									<Skeleton class="h-3 w-1/3" />
								</div>
								<Skeleton class="h-6 w-16 rounded-full" />
							</div>
						{/each}
					</div>
				{:else if foundItems.length === 0}
					<div class="text-center py-16">
						<div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-muted mb-4">
							<Package class="h-10 w-10 text-muted-foreground" />
						</div>
						<p class="text-muted-foreground font-semibold text-lg">No found items yet</p>
						<p class="text-sm text-muted-foreground mt-2">Check back later for new items</p>
					</div>
				{:else}
					<div class="space-y-3">
						{#each foundItems as item}
							<button
								type="button"
								class="flex items-start gap-3 sm:gap-4 p-3 sm:p-4 border rounded-lg hover:bg-muted/50 hover:border-primary/20 active:bg-muted cursor-pointer transition-all duration-200 w-full text-left group touch-manipulation"
								onclick={() => goto(`/dashboard/found`)}
							>
								{#if item.image_url}
									<div class="w-12 h-12 sm:w-16 sm:h-16 bg-muted overflow-hidden rounded-md flex items-center justify-center flex-shrink-0">
										<img
											src={getImageUrl(item.image_url)}
											alt={item.description}
											class="max-w-full max-h-full object-contain"
										/>
									</div>
								{:else}
									<div class="w-12 h-12 sm:w-16 sm:h-16 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
										<Package class="h-6 w-6 sm:h-8 sm:w-8 text-muted-foreground" />
									</div>
								{/if}
								<div class="flex-1 min-w-0">
									<p class="font-medium truncate text-sm sm:text-base">{item.description}</p>
									<p class="text-xs sm:text-sm text-muted-foreground">{item.location}</p>
									<p class="text-xs text-muted-foreground mt-1">{formatDate(item.reported_at)}</p>
								</div>
								<Badge variant="secondary" class="text-xs flex-shrink-0">{item.status}</Badge>
							</button>
						{/each}
					</div>
					<Button variant="outline" class="w-full mt-4" onclick={() => goto('/dashboard/found')}>
						View All Found Items
					</Button>
				{/if}
			</CardContent>
		</Card>

		<Card class="hover:shadow-lg transition-shadow duration-200">
			<CardHeader>
				<CardTitle class="text-xl">Pending Matches</CardTitle>
				<CardDescription class="text-base">Items that might match your lost items</CardDescription>
			</CardHeader>
			<CardContent>
				{#if loading}
					<div class="space-y-4">
						{#each Array(2) as _}
							<div class="p-4 space-y-3">
								<Skeleton class="h-4 w-full" />
								<Skeleton class="h-3 w-3/4" />
								<Skeleton class="h-3 w-1/2" />
							</div>
						{/each}
					</div>
				{:else if matches.filter((m) => m.match_status === 'PENDING').length === 0}
					<div class="text-center py-16">
						<div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-muted mb-4">
							<CheckCircle class="h-10 w-10 text-muted-foreground" />
						</div>
						<p class="text-muted-foreground font-semibold text-lg">No pending matches</p>
						<p class="text-sm text-muted-foreground mt-2">We'll notify you when matches are found</p>
					</div>
				{:else}
					<div class="space-y-3">
						{#each matches.filter((m) => m.match_status === 'PENDING') as match}
							<button
								type="button"
								class="w-full p-4 border rounded-lg hover:bg-muted/50 hover:border-primary/20 cursor-pointer transition-all duration-200 text-left group"
								onclick={() => goto('/dashboard/matches')}
							>
								<div class="flex items-start justify-between gap-4">
									<div class="flex-1 min-w-0">
										<p class="font-medium truncate">{match.lost_item.description}</p>
										<p class="text-sm text-muted-foreground">Found: {match.found_item.description}</p>
										<p class="text-xs text-muted-foreground mt-1">
											Confidence: {(match.confidence_score * 100).toFixed(0)}%
										</p>
									</div>
									<Badge variant="outline">{(match.confidence_score * 100).toFixed(0)}%</Badge>
								</div>
							</button>
						{/each}
					</div>
					<Button variant="outline" class="w-full mt-4" onclick={() => goto('/dashboard/matches')}>
						View All Matches
					</Button>
				{/if}
			</CardContent>
		</Card>
	</div>
</div>

