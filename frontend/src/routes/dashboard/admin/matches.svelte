<script lang="ts">
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { Input } from '$lib/components/ui/input';
	import * as Accordion from '$lib/components/ui/accordion';
	import { getMatches } from '$lib/api/admin';
	import { getImageUrl } from '$lib/api/config';
	import { onMount } from 'svelte';
	import type { Match } from '$lib/api/matches';
	import { CheckCircle, Search, X, Filter, Package, User, MapPin, Calendar, Percent, ZoomIn } from "@lucide/svelte";
	import * as Dialog from '$lib/components/ui/dialog';

	let matches = $state<Match[]>([]);
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
				match.lost_item.reported_by.name.toLowerCase().includes(query) ||
				match.found_item.reported_by.name.toLowerCase().includes(query) ||
				match.id.toLowerCase().includes(query)
			);
		}
		
		// Apply status filter
		if (statusFilter) {
			result = result.filter(match => match.match_status === statusFilter);
		}
		
		return result;
	});
	let loading = $state(false);
	let statusFilter = $state<string>('');
	let searchQuery = $state('');
	let imageModalOpen = $state(false);
	let selectedImageUrl = $state<string | null>(null);
	let selectedImageAlt = $state<string>('');

	onMount(async () => {
		await loadMatches();
	});

	async function loadMatches() {
		loading = true;
		try {
			matches = await getMatches({
				limit: 200,
				status: undefined
			});
		} catch (err) {
			console.error('Failed to load matches:', err);
		} finally {
			loading = false;
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

	function clearSearch() {
		searchQuery = '';
	}

	function openImageModal(imageUrl: string, alt: string, event?: MouseEvent) {
		if (event) {
			event.stopPropagation();
		}
		selectedImageUrl = imageUrl;
		selectedImageAlt = alt;
		imageModalOpen = true;
	}
</script>

<Card>
	<CardHeader>
		<div class="flex flex-col gap-4">
			<div class="flex items-center justify-between">
				<CardTitle class="flex items-center gap-2">
					<CheckCircle class="h-5 w-5" />
					Matches ({filteredMatches.length})
				</CardTitle>
			</div>
			<div class="flex flex-col sm:flex-row gap-2 sm:gap-3">
				<div class="relative flex-1">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
					<Input
						type="text"
						placeholder="Search by description, location, reporter, match ID..."
						bind:value={searchQuery}
						class="pl-9 pr-9 text-sm"
					/>
					{#if searchQuery}
						<button
							onclick={clearSearch}
							class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground touch-manipulation"
							aria-label="Clear search"
						>
							<X class="h-4 w-4" />
						</button>
					{/if}
				</div>
				<Select
					type="single"
					bind:value={statusFilter}
				>
					<SelectTrigger class="w-full sm:w-[180px] text-sm">
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
		</div>
	</CardHeader>
	<CardContent>
		{#if loading}
			<div class="text-center py-8 text-muted-foreground">Loading matches...</div>
		{:else if filteredMatches.length === 0}
			<div class="text-center py-8 text-muted-foreground">
				{searchQuery || statusFilter 
					? 'No matches found matching your filters' 
					: 'No matches found'}
			</div>
		{:else}
			<Accordion.Root type="multiple" class="space-y-4">
				{#each filteredMatches as match}
					<Accordion.Item value={match.id} class="border rounded-lg overflow-hidden">
						<Accordion.Trigger class="px-3 sm:px-4 py-2 sm:py-3 hover:bg-muted/50 transition-colors">
							<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-3 w-full">
								<div class="flex-1 min-w-0 text-left">
									<p class="text-sm sm:text-base font-medium break-words">Match #{match.id.slice(0, 8)}</p>
									<p class="text-xs sm:text-sm text-muted-foreground">Created: {formatDate(match.created_at)}</p>
								</div>
								<div class="flex flex-row gap-2 flex-shrink-0 items-center">
									<Badge
										variant={
											match.match_status === 'APPROVED'
												? 'default'
												: match.match_status === 'REJECTED'
													? 'destructive'
													: 'outline'
										}
										class="text-xs"
									>
										{match.match_status}
									</Badge>
									<Badge variant="secondary" class="text-xs">
										{(match.confidence_score * 100).toFixed(0)}% confidence
									</Badge>
								</div>
							</div>
						</Accordion.Trigger>
						<Accordion.Content class="px-3 sm:px-4 pb-3 sm:pb-4">
							<div class="space-y-4 sm:space-y-6 pt-3 sm:pt-4">
								<!-- Match Info -->
								<div class="p-3 sm:p-4 bg-muted/30 rounded-lg">
									<div class="flex flex-wrap items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
										<Badge
											variant={
												match.match_status === 'APPROVED'
													? 'default'
													: match.match_status === 'REJECTED'
														? 'destructive'
														: 'outline'
											}
										>
											{match.match_status}
										</Badge>
										<Badge variant="secondary" class="flex items-center gap-1">
											<Percent class="h-3 w-3" />
											{(match.confidence_score * 100).toFixed(1)}% Confidence
										</Badge>
										<span class="text-sm text-muted-foreground flex items-center gap-1">
											<Calendar class="h-3 w-3" />
											Created: {formatDate(match.created_at)}
										</span>
									</div>
									<p class="text-xs font-mono text-muted-foreground">Match ID: {match.id}</p>
								</div>

								<!-- Items Side by Side -->
								<div class="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
									<!-- Lost Item Details -->
									<div class="border rounded-lg p-4 lg:p-5">
									<h3 class="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center gap-2">
										<Package class="h-4 w-4 sm:h-5 sm:w-5" />
										Lost Item
									</h3>
										<div class="space-y-3 lg:space-y-4">
											{#if match.lost_item.image_url}
												<button
													type="button"
													class="relative w-full h-48 sm:h-56 lg:h-64 bg-muted overflow-hidden rounded-md flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
													onclick={(e) => openImageModal(getImageUrl(match.lost_item.image_url!), match.lost_item.description, e)}
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
											<div class="space-y-2 lg:space-y-3">
												<div>
													<p class="text-xs sm:text-sm font-medium text-muted-foreground mb-1">Description</p>
													<p class="text-sm sm:text-base break-words">{match.lost_item.description}</p>
												</div>
												<div>
													<p class="text-xs sm:text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
														<MapPin class="h-3 w-3 sm:h-4 sm:w-4" />
														Location
													</p>
													<p class="text-sm sm:text-base break-words">{match.lost_item.location}</p>
												</div>
												<div>
													<p class="text-xs sm:text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
														<Calendar class="h-3 w-3 sm:h-4 sm:w-4" />
														Reported At
													</p>
													<p class="text-sm sm:text-base">{formatDate(match.lost_item.reported_at)}</p>
												</div>
												<div>
													<p class="text-xs sm:text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
														<User class="h-3 w-3 sm:h-4 sm:w-4" />
														Reported By
													</p>
													<p class="text-sm sm:text-base break-words">{match.lost_item.reported_by.name}</p>
													<p class="text-xs sm:text-sm text-muted-foreground break-all">{match.lost_item.reported_by.email}</p>
													<p class="text-xs sm:text-sm text-muted-foreground">{match.lost_item.reported_by.contact_number}</p>
												</div>
												<div class="flex flex-wrap gap-2">
													<Badge variant={match.lost_item.status === 'LOST' ? 'destructive' : 'default'}>
														{match.lost_item.status}
													</Badge>
													{#if !match.lost_item.is_active}
														<Badge variant="secondary">Archived</Badge>
													{/if}
													{#if match.lost_item.is_admin_report}
														<Badge variant="outline">Admin Report</Badge>
													{/if}
												</div>
												<p class="text-xs font-mono text-muted-foreground break-all">Item ID: {match.lost_item.id}</p>
											</div>
										</div>
									</div>

									<!-- Found Item Details -->
									<div class="border rounded-lg p-4 lg:p-5">
										<h3 class="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center gap-2">
											<Package class="h-4 w-4 sm:h-5 sm:w-5" />
											Found Item
										</h3>
										<div class="space-y-3 lg:space-y-4">
											{#if match.found_item.image_url}
												<button
													type="button"
													class="relative w-full h-48 sm:h-56 lg:h-64 bg-muted overflow-hidden rounded-md flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
													onclick={(e) => openImageModal(getImageUrl(match.found_item.image_url!), match.found_item.description, e)}
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
											<div class="space-y-2 lg:space-y-3">
												<div>
													<p class="text-xs sm:text-sm font-medium text-muted-foreground mb-1">Description</p>
													<p class="text-sm sm:text-base break-words">{match.found_item.description}</p>
												</div>
												<div>
													<p class="text-xs sm:text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
														<MapPin class="h-3 w-3 sm:h-4 sm:w-4" />
														Location
													</p>
													<p class="text-sm sm:text-base break-words">{match.found_item.location}</p>
												</div>
												<div>
													<p class="text-xs sm:text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
														<Calendar class="h-3 w-3 sm:h-4 sm:w-4" />
														Reported At
													</p>
													<p class="text-sm sm:text-base">{formatDate(match.found_item.reported_at)}</p>
												</div>
												<div>
													<p class="text-xs sm:text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
														<User class="h-3 w-3 sm:h-4 sm:w-4" />
														Reported By
													</p>
													<p class="text-sm sm:text-base break-words">{match.found_item.reported_by.name}</p>
													<p class="text-xs sm:text-sm text-muted-foreground break-all">{match.found_item.reported_by.email}</p>
													<p class="text-xs sm:text-sm text-muted-foreground">{match.found_item.reported_by.contact_number}</p>
												</div>
												<div class="flex flex-wrap gap-2">
													<Badge variant={match.found_item.status === 'LOST' ? 'destructive' : 'default'}>
														{match.found_item.status}
													</Badge>
													{#if !match.found_item.is_active}
														<Badge variant="secondary">Archived</Badge>
													{/if}
													{#if match.found_item.is_admin_report}
														<Badge variant="outline">Admin Report</Badge>
													{/if}
												</div>
												<p class="text-xs font-mono text-muted-foreground break-all">Item ID: {match.found_item.id}</p>
											</div>
										</div>
									</div>
								</div>
							</div>
						</Accordion.Content>
					</Accordion.Item>
				{/each}
			</Accordion.Root>
		{/if}
	</CardContent>
</Card>

<!-- Image Modal -->
<Dialog.Root bind:open={imageModalOpen}>
	<Dialog.Content class="max-w-6xl w-[95vw] max-h-[95vh] p-0" showCloseButton={true}>
		{#if selectedImageUrl}
			<div class="relative w-full h-full flex items-center justify-center bg-muted p-6 min-h-[60vh]">
				<img
					src={selectedImageUrl}
					alt={selectedImageAlt}
					class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-lg"
				/>
			</div>
		{/if}
	</Dialog.Content>
</Dialog.Root>

