<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { getMyMatches, approveMatch, rejectMatch } from '$lib/api/matches';
	import { getImageUrl } from '$lib/api/config';
	import { onMount, onDestroy } from 'svelte';
	import type { Match } from '$lib/api/matches';
	import {
		AlertDialog,
		AlertDialogAction,
		AlertDialogCancel,
		AlertDialogContent,
		AlertDialogDescription,
		AlertDialogFooter,
		AlertDialogHeader,
		AlertDialogTitle
	} from '$lib/components/ui/alert-dialog';
	import { CheckCircle, X, Package, MapPin, Calendar, UserCheck, UserX, ZoomIn, Search, Filter, Shield } from "@lucide/svelte";
	import { Input } from '$lib/components/ui/input';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { Dialog, DialogContent } from '$lib/components/ui/dialog';
	import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '$lib/components/ui/accordion';
	import { getUserContext } from '$lib/contexts/user.svelte';
	import { toast } from 'svelte-sonner';
	import { Skeleton } from '$lib/components/ui/skeleton';

	const userContext = getUserContext();

	let matches = $state<Match[]>([]);
	let loading = $state(false);
	let selectedMatch = $state<Match | null>(null);
	let approveDialogOpen = $state(false);
	let rejectDialogOpen = $state(false);
	let actionLoading = $state(false);
	let imageModalOpen = $state(false);
	let selectedImageUrl = $state<string | null>(null);
	let selectedImageAlt = $state<string>('');
	let searchQuery = $state('');
	let statusFilter = $state<string>('');

	let pollInterval: ReturnType<typeof setInterval> | null = null;

	onMount(async () => {
		await loadMatches();
		
		// Poll for new matches every 30 seconds (reduced frequency to avoid visible refreshes)
		pollInterval = setInterval(() => {
			checkForNewMatches();
		}, 10000);
	});

	onDestroy(() => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}
	});

	async function loadMatches() {
		loading = true;
		try {
			const newMatches = await getMyMatches();
			matches = newMatches;
		} catch (err) {
			console.error('Failed to load matches:', err);
		} finally {
			loading = false;
		}
	}

	async function checkForNewMatches() {
		// Silent polling - only update if data changed, don't show loading state
		try {
			const previousMatchIds = new Set(matches.map(m => m.id));
			const previousMatchStatuses = new Map(matches.map(m => [m.id, m.match_status]));
			const newMatches = await getMyMatches();
			const newMatchIds = new Set(newMatches.map(m => m.id));
			
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
				
				if (newlyCreatedMatches.length > 0 && matches.length > 0) {
					// Only show toast if we already had matches loaded (not initial load)
					toast.info(`New match${newlyCreatedMatches.length !== 1 ? 'es' : ''} found!`, {
						description: `${newlyCreatedMatches.length} potential match${newlyCreatedMatches.length !== 1 ? 'es' : ''} ${newlyCreatedMatches.length !== 1 ? 'are' : 'is'} waiting for your review.`,
						duration: 5000
					});
				}
				
				// Update matches silently
				matches = newMatches;
			}
		} catch (err) {
			console.error('Failed to check for new matches:', err);
		}
	}

	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	let successMessage = $state<string | null>(null);
	let errorMessage = $state<string | null>(null);

	async function handleApprove() {
		if (!selectedMatch) return;
		actionLoading = true;
		errorMessage = null;
		successMessage = null;
		try {
			const response = await approveMatch(selectedMatch.id);
			successMessage = `Match approved! Contact information has been shared. Contact: ${response.contact_shared_with_finder.name} (${response.contact_shared_with_finder.contact_number})`;
			toast.success('Match approved!', {
				description: `Contact information shared: ${response.contact_shared_with_finder.name} (${response.contact_shared_with_finder.contact_number})`,
				duration: 5000
			});
			await loadMatches();
			await userContext.refreshMatches();
			approveDialogOpen = false;
			selectedMatch = null;
			// Clear success message after 5 seconds
			setTimeout(() => {
				successMessage = null;
			}, 5000);
		} catch (err) {
			const errMsg = err instanceof Error ? err.message : 'Failed to approve match';
			errorMessage = errMsg;
			toast.error('Failed to approve match', {
				description: errMsg
			});
			setTimeout(() => {
				errorMessage = null;
			}, 5000);
		} finally {
			actionLoading = false;
		}
	}

	async function handleReject() {
		if (!selectedMatch) return;
		actionLoading = true;
		errorMessage = null;
		successMessage = null;
		try {
			await rejectMatch(selectedMatch.id);
			successMessage = 'Match rejected successfully.';
			toast.success('Match rejected', {
				description: 'The match has been rejected successfully.'
			});
			await loadMatches();
			await userContext.refreshMatches();
			rejectDialogOpen = false;
			selectedMatch = null;
			setTimeout(() => {
				successMessage = null;
			}, 3000);
		} catch (err) {
			const errMsg = err instanceof Error ? err.message : 'Failed to reject match';
			errorMessage = errMsg;
			toast.error('Failed to reject match', {
				description: errMsg
			});
			setTimeout(() => {
				errorMessage = null;
			}, 5000);
		} finally {
			actionLoading = false;
		}
	}

	function openApproveDialog(match: Match) {
		selectedMatch = match;
		approveDialogOpen = true;
	}

	function openRejectDialog(match: Match) {
		selectedMatch = match;
		rejectDialogOpen = true;
	}

	function openImageModal(imageUrl: string, alt: string) {
		selectedImageUrl = imageUrl;
		selectedImageAlt = alt;
		imageModalOpen = true;
	}


	// Filter matches based on search and status
	let filteredMatches = $derived.by(() => {
		let result = matches;
		
		// Apply search filter
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase().trim();
			result = result.filter(match => 
				match.lost_item.description.toLowerCase().includes(query) ||
				match.found_item.description.toLowerCase().includes(query) ||
				match.lost_item.location.toLowerCase().includes(query) ||
				match.found_item.location.toLowerCase().includes(query) ||
				match.id.toLowerCase().includes(query)
			);
		}
		
		// Apply status filter
		if (statusFilter) {
			result = result.filter(match => match.match_status === statusFilter);
		}
		
		return result;
	});

	let pendingMatches = $derived(filteredMatches.filter((m) => m.match_status === 'PENDING'));
	let approvedMatches = $derived(filteredMatches.filter((m) => m.match_status === 'APPROVED'));
	let rejectedMatches = $derived(filteredMatches.filter((m) => m.match_status === 'REJECTED'));

	// Helper function to check if current user is the loser (can approve/reject)
	function isLoser(match: Match): boolean {
		return userContext.user?.id === match.loser_id;
	}

	function clearSearch() {
		searchQuery = '';
	}
</script>

<div class="space-y-8">
	<div class="space-y-2">
		<h1 class="text-3xl md:text-4xl font-bold tracking-tight">My Matches</h1>
		<p class="text-muted-foreground text-lg">Review potential matches for your items</p>
	</div>

	<!-- Search and Filters -->
	<div class="flex flex-col sm:flex-row gap-3">
		<div class="relative flex-1">
			<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
			<Input
				type="text"
				placeholder="Search by description, location, match ID..."
				bind:value={searchQuery}
				class="pl-9 pr-9"
			/>
			{#if searchQuery}
				<button
					onclick={clearSearch}
					class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
				>
					<X class="h-4 w-4" />
				</button>
			{/if}
		</div>
		<Select
			type="single"
			bind:value={statusFilter}
		>
			<SelectTrigger class="w-full sm:w-[180px]">
				<Filter class="h-4 w-4 mr-2" />
				{statusFilter || 'All Status'}
			</SelectTrigger>
			<SelectContent>
				<SelectItem value="">All Status</SelectItem>
				<SelectItem value="PENDING">Pending</SelectItem>
				<SelectItem value="APPROVED">Approved</SelectItem>
				<SelectItem value="REJECTED">Rejected</SelectItem>
			</SelectContent>
		</Select>
	</div>

	<!-- Privacy Notice -->
	<div class="flex items-start gap-2 p-3 text-sm bg-blue-50 dark:bg-blue-950/30 rounded-md border border-blue-200 dark:border-blue-800">
		<Shield class="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
		<div>
			<p class="font-medium text-blue-900 dark:text-blue-100">Privacy Protected</p>
			<p class="text-blue-700 dark:text-blue-300 text-xs mt-1">
				Contact information is only shared after a match is approved by the item owner. Until then, all personal details remain private.
			</p>
		</div>
	</div>

	{#if successMessage}
		<div class="flex items-center gap-2 p-3 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30 rounded-md border border-green-200 dark:border-green-800">
			<CheckCircle class="h-4 w-4" />
			<span>{successMessage}</span>
		</div>
	{/if}

		{#if errorMessage}
			<div class="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md border border-destructive/20">
				<X class="h-4 w-4" />
				<span>{errorMessage}</span>
			</div>
		{/if}

	{#if loading}
		<div class="space-y-4">
			{#each Array(2) as _}
				<Card>
					<CardHeader>
						<div class="flex items-start justify-between">
							<div class="flex-1 space-y-2">
								<Skeleton class="h-6 w-48" />
								<Skeleton class="h-4 w-32" />
							</div>
							<Skeleton class="h-6 w-16 rounded-full" />
						</div>
					</CardHeader>
					<CardContent>
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div class="space-y-2">
								<Skeleton class="h-4 w-24" />
								<Skeleton class="h-3 w-full" />
								<Skeleton class="h-3 w-3/4" />
							</div>
							<div class="space-y-2">
								<Skeleton class="h-4 w-24" />
								<Skeleton class="h-3 w-full" />
								<Skeleton class="h-3 w-3/4" />
							</div>
						</div>
						<Skeleton class="h-10 w-full mt-4" />
					</CardContent>
				</Card>
			{/each}
		</div>
	{:else if filteredMatches.length === 0}
		<Card>
			<CardContent class="py-16 text-center">
				<Package class="h-16 w-16 text-muted-foreground mx-auto mb-4 opacity-50" />
				<p class="text-muted-foreground font-medium text-lg mb-1">
					{searchQuery || statusFilter ? 'No matches found matching your filters' : 'No matches found yet'}
				</p>
				<p class="text-sm text-muted-foreground">
					{searchQuery || statusFilter ? 'Try adjusting your search or filters' : "We'll notify you when potential matches are found for your items."}
				</p>
			</CardContent>
		</Card>
	{:else}
		{#if pendingMatches.length > 0}
			<div class="space-y-4">
				<h2 class="text-xl font-semibold">Pending Matches</h2>
				{#each pendingMatches as match}
					<Card class="hover:shadow-lg transition-shadow duration-200 border-2">
						<CardHeader>
							<div class="flex items-start justify-between">
								<div>
									<CardTitle class="flex items-center gap-2">
										Match Found
										{#if isLoser(match)}
											<Badge variant="default" class="text-xs">
												<UserCheck class="h-3 w-3 mr-1" />
												You are the owner
											</Badge>
										{:else}
											<Badge variant="secondary" class="text-xs">
												<UserX class="h-3 w-3 mr-1" />
												You found this item
											</Badge>
										{/if}
									</CardTitle>
									<CardDescription>
										Confidence Score: {(match.confidence_score * 100).toFixed(0)}%
									</CardDescription>
								</div>
								<Badge variant="outline" class="text-lg">
									{(match.confidence_score * 100).toFixed(0)}%
								</Badge>
							</div>
						</CardHeader>
						<CardContent>
							<div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-4">
								<div>
									<h3 class="font-semibold mb-2 flex items-center gap-2 text-sm md:text-base">
										<Package class="h-4 w-4 flex-shrink-0" />
										Your Lost Item
									</h3>
									<div class="space-y-2 pl-6">
										<p class="text-sm break-words">{match.lost_item.description}</p>
										<div class="flex items-center gap-2 text-xs text-muted-foreground">
											<MapPin class="h-3 w-3 flex-shrink-0" />
											<span>{match.lost_item.location}</span>
										</div>
										<div class="flex items-center gap-2 text-xs text-muted-foreground">
											<Calendar class="h-3 w-3 flex-shrink-0" />
											<span>{formatDate(match.lost_item.reported_at)}</span>
										</div>
									</div>
									{#if match.lost_item.image_url}
										<button
											type="button"
											class="relative w-full h-32 sm:h-40 bg-muted overflow-hidden rounded-md mt-2 flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
											onclick={(e) => {
												e.stopPropagation();
												openImageModal(getImageUrl(match.lost_item.image_url), match.lost_item.description);
											}}
										>
											<img
												src={getImageUrl(match.lost_item.image_url)}
												alt={match.lost_item.description}
												class="max-w-full max-h-full object-contain"
											/>
											<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
												<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
											</div>
										</button>
									{/if}
								</div>
								<div>
									<h3 class="font-semibold mb-2 flex items-center gap-2 text-sm md:text-base">
										<Package class="h-4 w-4 flex-shrink-0" />
										Found Item
									</h3>
									<div class="space-y-2 pl-6">
										<p class="text-sm break-words">{match.found_item.description}</p>
										<div class="flex items-center gap-2 text-xs text-muted-foreground">
											<MapPin class="h-3 w-3 flex-shrink-0" />
											<span>{match.found_item.location}</span>
										</div>
										<div class="flex items-center gap-2 text-xs text-muted-foreground">
											<Calendar class="h-3 w-3 flex-shrink-0" />
											<span>{formatDate(match.found_item.reported_at)}</span>
										</div>
									</div>
									{#if match.found_item.image_url}
										<button
											type="button"
											class="relative w-full h-32 sm:h-40 bg-muted overflow-hidden rounded-md mt-2 flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
											onclick={(e) => {
												e.stopPropagation();
												openImageModal(getImageUrl(match.found_item.image_url), match.found_item.description);
											}}
										>
											<img
												src={getImageUrl(match.found_item.image_url)}
												alt={match.found_item.description}
												class="max-w-full max-h-full object-contain"
											/>
											<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
												<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
											</div>
										</button>
									{/if}
								</div>
							</div>
							{#if isLoser(match)}
								<div class="flex flex-col sm:flex-row gap-2">
									<Button
										variant="default"
										onclick={() => openApproveDialog(match)}
										class="flex-1"
									>
										<CheckCircle class="h-4 w-4 mr-2" />
										<span class="hidden sm:inline">Approve Match</span>
										<span class="sm:hidden">Approve</span>
									</Button>
									<Button
										variant="outline"
										onclick={() => openRejectDialog(match)}
										class="flex-1"
									>
										<X class="h-4 w-4 mr-2" />
										<span class="hidden sm:inline">Reject Match</span>
										<span class="sm:hidden">Reject</span>
									</Button>
								</div>
							{:else}
								<div class="p-3 bg-muted rounded-md text-sm text-muted-foreground text-center">
									Waiting for the owner to approve or reject this match. You'll be notified when they respond.
								</div>
							{/if}
						</CardContent>
					</Card>
				{/each}
			</div>
		{/if}

		{#if approvedMatches.length > 0}
			<div class="space-y-4">
				<h2 class="text-xl font-semibold">Approved Matches</h2>
				<Accordion type="single" class="w-full space-y-4">
					{#each approvedMatches as match}
						<AccordionItem value={match.id} class="border-0 rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
							<AccordionTrigger class="px-6 py-4 hover:no-underline">
								<div class="flex items-center gap-4 w-full pr-4">
									{#if match.lost_item.image_url || match.found_item.image_url}
										<div class="flex gap-2 flex-shrink-0">
											{#if match.lost_item.image_url}
												<div class="w-16 h-16 bg-muted rounded-md overflow-hidden flex items-center justify-center">
													<img
														src={getImageUrl(match.lost_item.image_url)}
														alt={match.lost_item.description}
														class="w-full h-full object-cover"
													/>
												</div>
											{/if}
											{#if match.found_item.image_url}
												<div class="w-16 h-16 bg-muted rounded-md overflow-hidden flex items-center justify-center">
													<img
														src={getImageUrl(match.found_item.image_url)}
														alt={match.found_item.description}
														class="w-full h-full object-cover"
													/>
												</div>
											{/if}
										</div>
									{/if}
									<div class="flex items-center justify-between flex-1 min-w-0">
										<div class="text-left min-w-0">
											<p class="font-medium truncate">{match.lost_item.description}</p>
											<p class="text-sm text-muted-foreground truncate">
												Matched with: {match.found_item.description}
											</p>
										</div>
										<Badge variant="default" class="ml-auto mr-2 flex-shrink-0">Approved</Badge>
									</div>
								</div>
							</AccordionTrigger>
							<AccordionContent class="px-6 pb-6">
								<div class="space-y-4 pt-2">
									<!-- Match Info -->
									<div class="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
										<div class="flex items-center gap-2 mb-2">
											<CheckCircle class="h-5 w-5 text-green-600 dark:text-green-400" />
											<p class="font-semibold text-green-900 dark:text-green-100">Match Approved</p>
										</div>
										<div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
											<div>
												<p class="text-green-700 dark:text-green-300 font-medium mb-1">Confidence Score</p>
												<p class="text-green-900 dark:text-green-100 text-lg font-semibold">
													{(match.confidence_score * 100).toFixed(0)}%
												</p>
											</div>
											<div>
												<p class="text-green-700 dark:text-green-300 font-medium mb-1">Approved At</p>
												<p class="text-green-900 dark:text-green-100">{formatDate(match.created_at)}</p>
											</div>
										</div>
									</div>

									<!-- Lost Item Details -->
									<div class="space-y-2">
										<h3 class="text-base font-semibold flex items-center gap-2">
											<Package class="h-4 w-4" />
											Your Lost Item
										</h3>
										<Card>
											<CardContent class="p-4 space-y-2">
												{#if match.lost_item.image_url}
													<button
														type="button"
														class="relative w-full h-48 bg-muted overflow-hidden rounded-lg flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group mb-2"
														onclick={() => openImageModal(getImageUrl(match.lost_item.image_url!), match.lost_item.description)}
													>
														<img
															src={getImageUrl(match.lost_item.image_url)}
															alt={match.lost_item.description}
															class="max-w-full max-h-full object-contain"
														/>
														<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
															<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
														</div>
													</button>
												{/if}
												<div>
													<p class="text-sm font-medium text-muted-foreground mb-1">Description</p>
													<p class="text-sm">{match.lost_item.description}</p>
												</div>
												<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
													<div>
														<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
															<MapPin class="h-3 w-3" />
															Location
														</p>
														<p class="text-sm">{match.lost_item.location}</p>
													</div>
													<div>
														<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
															<Calendar class="h-3 w-3" />
															Reported At
														</p>
														<p class="text-sm">{formatDate(match.lost_item.reported_at)}</p>
													</div>
												</div>
											</CardContent>
										</Card>
									</div>

									<!-- Found Item Details -->
									<div class="space-y-2">
										<h3 class="text-base font-semibold flex items-center gap-2">
											<Package class="h-4 w-4" />
											Found Item
										</h3>
										<Card>
											<CardContent class="p-4 space-y-2">
												{#if match.found_item.image_url}
													<button
														type="button"
														class="relative w-full h-48 bg-muted overflow-hidden rounded-lg flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group mb-2"
														onclick={() => openImageModal(getImageUrl(match.found_item.image_url!), match.found_item.description)}
													>
														<img
															src={getImageUrl(match.found_item.image_url)}
															alt={match.found_item.description}
															class="max-w-full max-h-full object-contain"
														/>
														<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
															<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
														</div>
													</button>
												{/if}
												<div>
													<p class="text-sm font-medium text-muted-foreground mb-1">Description</p>
													<p class="text-sm">{match.found_item.description}</p>
												</div>
												<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
													<div>
														<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
															<MapPin class="h-3 w-3" />
															Location Found
														</p>
														<p class="text-sm">{match.found_item.location}</p>
													</div>
													<div>
														<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
															<Calendar class="h-3 w-3" />
															Reported At
														</p>
														<p class="text-sm">{formatDate(match.found_item.reported_at)}</p>
													</div>
												</div>
											</CardContent>
										</Card>
									</div>

									<!-- Match ID -->
									<div>
										<p class="text-sm font-medium text-muted-foreground mb-1">Match ID</p>
										<p class="text-xs font-mono text-muted-foreground break-all">{match.id}</p>
									</div>
								</div>
							</AccordionContent>
						</AccordionItem>
					{/each}
				</Accordion>
			</div>
		{/if}

		{#if rejectedMatches.length > 0}
			<div class="space-y-4">
				<h2 class="text-xl font-semibold">Rejected Matches</h2>
				<Accordion type="single" class="w-full space-y-4">
				{#each rejectedMatches as match}
						<AccordionItem value={match.id} class="border-0 rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
							<AccordionTrigger class="px-6 py-4 hover:no-underline">
								<div class="flex items-center gap-4 w-full pr-4">
									{#if match.lost_item.image_url || match.found_item.image_url}
										<div class="flex gap-2 flex-shrink-0">
											{#if match.lost_item.image_url}
												<div class="w-16 h-16 bg-muted rounded-md overflow-hidden flex items-center justify-center">
													<img
														src={getImageUrl(match.lost_item.image_url)}
														alt={match.lost_item.description}
														class="w-full h-full object-cover"
													/>
												</div>
											{/if}
											{#if match.found_item.image_url}
												<div class="w-16 h-16 bg-muted rounded-md overflow-hidden flex items-center justify-center">
													<img
														src={getImageUrl(match.found_item.image_url)}
														alt={match.found_item.description}
														class="w-full h-full object-cover"
													/>
												</div>
											{/if}
										</div>
									{/if}
									<div class="flex items-center justify-between flex-1 min-w-0">
										<div class="text-left min-w-0">
											<p class="font-medium truncate">{match.lost_item.description}</p>
											<p class="text-sm text-muted-foreground truncate">
										Matched with: {match.found_item.description}
									</p>
										</div>
										<Badge variant="secondary" class="ml-auto mr-2 flex-shrink-0">Rejected</Badge>
									</div>
								</div>
							</AccordionTrigger>
							<AccordionContent class="px-6 pb-6">
								<div class="space-y-4 pt-2">
									<!-- Match Info -->
									<div class="p-4 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-800">
										<div class="flex items-center gap-2 mb-2">
											<X class="h-5 w-5 text-red-600 dark:text-red-400" />
											<p class="font-semibold text-red-900 dark:text-red-100">Match Rejected</p>
										</div>
										<div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
											<div>
												<p class="text-red-700 dark:text-red-300 font-medium mb-1">Confidence Score</p>
												<p class="text-red-900 dark:text-red-100 text-lg font-semibold">
													{(match.confidence_score * 100).toFixed(0)}%
												</p>
											</div>
											<div>
												<p class="text-red-700 dark:text-red-300 font-medium mb-1">Rejected At</p>
												<p class="text-red-900 dark:text-red-100">{formatDate(match.created_at)}</p>
											</div>
										</div>
									</div>

									<!-- Lost Item Details -->
									<div class="space-y-2">
										<h3 class="text-base font-semibold flex items-center gap-2">
											<Package class="h-4 w-4" />
											Your Lost Item
										</h3>
										<Card>
											<CardContent class="p-4 space-y-2">
												{#if match.lost_item.image_url}
													<button
														type="button"
														class="relative w-full h-48 bg-muted overflow-hidden rounded-lg flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group mb-2"
														onclick={() => openImageModal(getImageUrl(match.lost_item.image_url!), match.lost_item.description)}
													>
														<img
															src={getImageUrl(match.lost_item.image_url)}
															alt={match.lost_item.description}
															class="max-w-full max-h-full object-contain"
														/>
														<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
															<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
														</div>
													</button>
												{/if}
												<div>
													<p class="text-sm font-medium text-muted-foreground mb-1">Description</p>
													<p class="text-sm">{match.lost_item.description}</p>
												</div>
												<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
													<div>
														<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
															<MapPin class="h-3 w-3" />
															Location
														</p>
														<p class="text-sm">{match.lost_item.location}</p>
													</div>
													<div>
														<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
															<Calendar class="h-3 w-3" />
															Reported At
														</p>
														<p class="text-sm">{formatDate(match.lost_item.reported_at)}</p>
													</div>
												</div>
											</CardContent>
										</Card>
									</div>

									<!-- Found Item Details -->
									<div class="space-y-2">
										<h3 class="text-base font-semibold flex items-center gap-2">
											<Package class="h-4 w-4" />
											Found Item
										</h3>
										<Card>
											<CardContent class="p-4 space-y-2">
												{#if match.found_item.image_url}
													<button
														type="button"
														class="relative w-full h-48 bg-muted overflow-hidden rounded-lg flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group mb-2"
														onclick={() => openImageModal(getImageUrl(match.found_item.image_url!), match.found_item.description)}
													>
														<img
															src={getImageUrl(match.found_item.image_url)}
															alt={match.found_item.description}
															class="max-w-full max-h-full object-contain"
														/>
														<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
															<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
														</div>
													</button>
												{/if}
												<div>
													<p class="text-sm font-medium text-muted-foreground mb-1">Description</p>
													<p class="text-sm">{match.found_item.description}</p>
												</div>
												<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
													<div>
														<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
															<MapPin class="h-3 w-3" />
															Location Found
														</p>
														<p class="text-sm">{match.found_item.location}</p>
													</div>
													<div>
														<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
															<Calendar class="h-3 w-3" />
															Reported At
														</p>
														<p class="text-sm">{formatDate(match.found_item.reported_at)}</p>
													</div>
							</div>
						</CardContent>
					</Card>
									</div>

									<!-- Match ID -->
									<div>
										<p class="text-sm font-medium text-muted-foreground mb-1">Match ID</p>
										<p class="text-xs font-mono text-muted-foreground break-all">{match.id}</p>
									</div>
								</div>
							</AccordionContent>
						</AccordionItem>
				{/each}
				</Accordion>
			</div>
		{/if}
	{/if}

	<AlertDialog bind:open={approveDialogOpen}>
		<AlertDialogContent>
			<AlertDialogHeader>
				<AlertDialogTitle>Approve Match?</AlertDialogTitle>
				<AlertDialogDescription>
					Are you sure you want to approve this match? This will archive both items and share contact
					information with both parties.
				</AlertDialogDescription>
			</AlertDialogHeader>
			<AlertDialogFooter>
				<AlertDialogCancel disabled={actionLoading}>Cancel</AlertDialogCancel>
				<AlertDialogAction onclick={handleApprove} disabled={actionLoading}>
					{actionLoading ? 'Approving...' : 'Approve'}
				</AlertDialogAction>
			</AlertDialogFooter>
		</AlertDialogContent>
	</AlertDialog>

	<AlertDialog bind:open={rejectDialogOpen}>
		<AlertDialogContent>
			<AlertDialogHeader>
				<AlertDialogTitle>Reject Match?</AlertDialogTitle>
				<AlertDialogDescription>
					Are you sure you want to reject this match? This will mark the match as rejected.
				</AlertDialogDescription>
			</AlertDialogHeader>
			<AlertDialogFooter>
				<AlertDialogCancel disabled={actionLoading}>Cancel</AlertDialogCancel>
				<AlertDialogAction onclick={handleReject} disabled={actionLoading} class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
					{actionLoading ? 'Rejecting...' : 'Reject'}
				</AlertDialogAction>
			</AlertDialogFooter>
		</AlertDialogContent>
	</AlertDialog>

	<!-- Image Modal -->
	<Dialog bind:open={imageModalOpen}>
		<DialogContent class="max-w-4xl max-h-[90vh] p-0" showCloseButton={true}>
			{#if selectedImageUrl}
				<div class="relative w-full h-full flex items-center justify-center bg-muted p-4">
					<img
						src={selectedImageUrl}
						alt={selectedImageAlt}
						class="max-w-full max-h-[85vh] object-contain rounded-lg"
					/>
				</div>
			{/if}
		</DialogContent>
	</Dialog>
</div>

