<script lang="ts">
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { Input } from '$lib/components/ui/input';
	import { getItems, getMatches } from '$lib/api/admin';
	import type { ItemsListParams } from '$lib/api/admin';
	import { getImageUrl } from '$lib/api/config';
	import { onMount } from 'svelte';
	import type { Item } from '$lib/api/items';
	import type { Match } from '$lib/api/matches';
	import { Package, Search, X, Filter, ZoomIn, ChevronUp, ChevronDown, CheckCircle2 } from "@lucide/svelte";
	import { Button } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog';

	type ItemGroup = {
		type: 'matched';
		lostItem: Item;
		foundItem: Item;
		matchId: string;
	} | {
		type: 'single';
		item: Item;
	};

	let items = $state<Item[]>([]);
	let matches = $state<Match[]>([]);
	let expandedGroups = $state<Set<string>>(new Set());
let serverSearchActive = $state(false);
	
	let itemGroups = $derived.by(() => {
		const groups: ItemGroup[] = [];
		const matchedItemIds = new Set<string>();
		const matchMap = new Map<string, { lostItem: Item; foundItem: Item; matchId: string }>();
		
		// Build map of matched items
		for (const match of matches) {
			if (match.match_status === 'APPROVED') {
				matchedItemIds.add(match.lost_item.id);
				matchedItemIds.add(match.found_item.id);
				matchMap.set(match.lost_item.id, {
					lostItem: match.lost_item,
					foundItem: match.found_item,
					matchId: match.id
				});
				matchMap.set(match.found_item.id, {
					lostItem: match.lost_item,
					foundItem: match.found_item,
					matchId: match.id
				});
			}
		}
		
		// Group items
		const processedItems = new Set<string>();
		for (const item of items) {
			if (processedItems.has(item.id)) continue;
			
			if (matchedItemIds.has(item.id) && matchMap.has(item.id)) {
				const matchData = matchMap.get(item.id)!;
				groups.push({
					type: 'matched',
					lostItem: matchData.lostItem,
					foundItem: matchData.foundItem,
					matchId: matchData.matchId
				});
				processedItems.add(matchData.lostItem.id);
				processedItems.add(matchData.foundItem.id);
			} else {
				groups.push({
					type: 'single',
					item
				});
				processedItems.add(item.id);
			}
		}
		
		return groups;
	});
	
	let filteredItemGroups = $derived.by(() => {
		let result = itemGroups;
		
		// Apply search filter
		if (searchQuery.trim() && !serverSearchActive) {
			const query = searchQuery.toLowerCase().trim();
			result = result.filter(group => {
				if (group.type === 'matched') {
					return (
						group.lostItem.description.toLowerCase().includes(query) ||
						group.lostItem.location.toLowerCase().includes(query) ||
						group.lostItem.reported_by.name.toLowerCase().includes(query) ||
						group.lostItem.reported_by.email.toLowerCase().includes(query) ||
						group.foundItem.description.toLowerCase().includes(query) ||
						group.foundItem.location.toLowerCase().includes(query) ||
						group.foundItem.reported_by.name.toLowerCase().includes(query) ||
						group.foundItem.reported_by.email.toLowerCase().includes(query)
					);
				} else {
					return (
						group.item.description.toLowerCase().includes(query) ||
						group.item.location.toLowerCase().includes(query) ||
						group.item.reported_by.name.toLowerCase().includes(query) ||
						group.item.reported_by.email.toLowerCase().includes(query)
					);
				}
			});
		}
		
		// Apply status filter
		if (statusFilter) {
			result = result.filter(group => {
				if (group.type === 'matched') {
					return group.lostItem.status === statusFilter || group.foundItem.status === statusFilter;
				} else {
					return group.item.status === statusFilter;
				}
			});
		}
		
		// Apply active filter
		if (activeFilter === 'active') {
			result = result.filter(group => {
				if (group.type === 'matched') {
					return group.lostItem.is_active || group.foundItem.is_active;
				} else {
					return group.item.is_active;
				}
			});
		} else if (activeFilter === 'archived') {
			result = result.filter(group => {
				if (group.type === 'matched') {
					return !group.lostItem.is_active && !group.foundItem.is_active;
				} else {
					return !group.item.is_active;
				}
			});
		}
		
		return result;
	});
	let loading = $state(false);
	let statusFilter = $state<string>('');
	let activeFilter = $state<string>('all');
	let searchQuery = $state('');
	let imageModalOpen = $state(false);
	let selectedImageUrl = $state<string | null>(null);
	let selectedImageAlt = $state<string>('');
let searchDebounce: ReturnType<typeof setTimeout> | undefined;

	onMount(async () => {
		await loadItems();
	});

$effect(() => {
	const trimmed = searchQuery.trim();
	if (searchDebounce) {
		clearTimeout(searchDebounce);
	}

	if (trimmed.length >= 2 || (trimmed.length === 0 && serverSearchActive)) {
		searchDebounce = setTimeout(() => {
			loadItems();
		}, 500);
	}
});

	async function loadItems() {
		loading = true;
		try {
		const trimmedQuery = searchQuery.trim();
		const includeArchived = activeFilter !== 'active';
		serverSearchActive = trimmedQuery.length >= 2;

		const itemParams: ItemsListParams = {
			limit: 200,
			status: statusFilter || undefined,
			include_archived: includeArchived
		};

		if (serverSearchActive) {
			itemParams.q = trimmedQuery;
			itemParams.include_matches = true;
		}

		[items, matches] = await Promise.all([
			getItems(itemParams),
				getMatches({
					limit: 200,
					status: 'APPROVED'
				})
			]);
		} catch (err) {
			console.error('Failed to load items:', err);
		} finally {
			loading = false;
		}
	}
	
	function toggleGroup(groupId: string) {
		expandedGroups = new Set(expandedGroups);
		if (expandedGroups.has(groupId)) {
			expandedGroups.delete(groupId);
		} else {
			expandedGroups.add(groupId);
		}
	}
	
	function isExpanded(groupId: string): boolean {
		return expandedGroups.has(groupId);
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
	
	function clearAllFilters() {
		searchQuery = '';
		statusFilter = '';
		activeFilter = 'all';
	}
	
	let hasActiveFilters = $derived(searchQuery.trim() !== '' || statusFilter !== '' || activeFilter !== 'all');

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
					<Package class="h-5 w-5" />
					Items ({filteredItemGroups.length})
				</CardTitle>
			</div>
			<div class="flex flex-col gap-3">
				<!-- Search Bar -->
				<div class="relative flex-1">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
					<Input
						type="text"
						placeholder="Search items by description, location, or reporter name..."
						bind:value={searchQuery}
						class="pl-9 pr-9 text-sm"
					/>
					{#if searchQuery}
						<button
							onclick={clearSearch}
							class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors touch-manipulation"
							aria-label="Clear search"
						>
							<X class="h-4 w-4" />
						</button>
					{/if}
				</div>
				
				<!-- Filters Row -->
				<div class="flex flex-wrap items-center gap-2">
					<Select
						type="single"
						bind:value={statusFilter}
					>
						<SelectTrigger class="w-full sm:w-[140px] text-sm">
							<Filter class="h-4 w-4 mr-2" />
							{statusFilter || 'Status'}
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="">All Status</SelectItem>
							<SelectItem value="LOST">Lost Items</SelectItem>
							<SelectItem value="FOUND">Found Items</SelectItem>
						</SelectContent>
					</Select>
					<Select
						type="single"
						bind:value={activeFilter}
					>
						<SelectTrigger class="w-full sm:w-[140px] text-sm">
							{activeFilter === 'all' ? 'All Items' : activeFilter === 'active' ? 'Active Only' : 'Archived Only'}
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="all">All Items</SelectItem>
							<SelectItem value="active">Active Only</SelectItem>
							<SelectItem value="archived">Archived Only</SelectItem>
						</SelectContent>
					</Select>
					
					{#if hasActiveFilters}
						<Button
							variant="ghost"
							size="sm"
							onclick={clearAllFilters}
							class="h-9 text-xs"
						>
							<X class="h-3 w-3 mr-1" />
							Clear filters
						</Button>
					{/if}
					
					<!-- Active Filter Badges -->
					{#if hasActiveFilters}
						<div class="flex flex-wrap gap-1.5 ml-auto">
							{#if searchQuery}
								<Badge variant="secondary" class="text-xs">
									Search: "{searchQuery}"
									<button
										onclick={clearSearch}
										class="ml-1.5 hover:text-destructive"
										aria-label="Remove search filter"
									>
										<X class="h-3 w-3" />
									</button>
								</Badge>
							{/if}
							{#if statusFilter}
								<Badge variant="secondary" class="text-xs">
									{statusFilter}
									<button
										onclick={() => statusFilter = ''}
										class="ml-1.5 hover:text-destructive"
										aria-label="Remove status filter"
									>
										<X class="h-3 w-3" />
									</button>
								</Badge>
							{/if}
							{#if activeFilter !== 'all'}
								<Badge variant="secondary" class="text-xs">
									{activeFilter === 'active' ? 'Active' : 'Archived'}
									<button
										onclick={() => activeFilter = 'all'}
										class="ml-1.5 hover:text-destructive"
										aria-label="Remove active filter"
									>
										<X class="h-3 w-3" />
									</button>
								</Badge>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</CardHeader>
	<CardContent>
		{#if loading}
			<div class="text-center py-8 text-muted-foreground">Loading items...</div>
		{:else if filteredItemGroups.length === 0}
			<div class="text-center py-8 text-muted-foreground">
				{searchQuery || statusFilter || activeFilter !== 'all' 
					? 'No items found matching your filters' 
					: 'No items found'}
			</div>
		{:else}
			<div class="space-y-4">
				{#each filteredItemGroups as group}
					{#if group.type === 'matched'}
						{@const groupId = group.matchId}
						{@const expanded = isExpanded(groupId)}
						<div class="border rounded-lg overflow-hidden transition-all">
							<!-- Stacked Card Header (Collapsed View) -->
							<button
								type="button"
								onclick={() => toggleGroup(groupId)}
								class="w-full p-4 hover:bg-muted/50 transition-colors flex items-center justify-between"
							>
								<div class="flex items-center gap-3 flex-1 min-w-0">
									<div class="relative flex-shrink-0">
										<!-- Stacked card effect -->
										<div class="relative w-20 h-20">
											{#if group.lostItem.image_url}
												<img
													src={getImageUrl(group.lostItem.image_url)}
													alt={group.lostItem.description}
													class="absolute top-0 left-0 w-16 h-16 rounded-md object-cover border-2 border-background shadow-md z-10"
												/>
											{:else}
												<div class="absolute top-0 left-0 w-16 h-16 bg-muted rounded-md flex items-center justify-center border-2 border-background shadow-md z-10">
													<Package class="h-6 w-6 text-muted-foreground" />
												</div>
											{/if}
											{#if group.foundItem.image_url}
												<img
													src={getImageUrl(group.foundItem.image_url)}
													alt={group.foundItem.description}
													class="absolute top-2 left-2 w-16 h-16 rounded-md object-cover border-2 border-background shadow-md"
												/>
											{:else}
												<div class="absolute top-2 left-2 w-16 h-16 bg-muted rounded-md flex items-center justify-center border-2 border-background shadow-md">
													<Package class="h-6 w-6 text-muted-foreground" />
												</div>
											{/if}
										</div>
									</div>
									<div class="flex-1 min-w-0 text-left">
										<div class="flex items-center gap-2 mb-1">
											<CheckCircle2 class="h-4 w-4 text-green-600 flex-shrink-0" />
											<p class="font-medium break-words text-base text-green-700 dark:text-green-400">Successfully Matched</p>
										</div>
										<p class="text-sm text-muted-foreground line-clamp-2">
											<span class="font-medium">Lost:</span> {group.lostItem.description} • 
											<span class="font-medium">Found:</span> {group.foundItem.description}
										</p>
									</div>
									<Badge variant="default" class="bg-green-600 hover:bg-green-700 flex-shrink-0">
										<CheckCircle2 class="h-3 w-3 mr-1" />
										Resolved
									</Badge>
									{#if expanded}
										<ChevronUp class="h-5 w-5 text-muted-foreground flex-shrink-0 ml-2" />
									{:else}
										<ChevronDown class="h-5 w-5 text-muted-foreground flex-shrink-0 ml-2" />
									{/if}
								</div>
							</button>
							
							<!-- Expanded View -->
							{#if expanded}
								<div class="border-t">
									{#if statusFilter === 'LOST'}
										<!-- Show only Lost Item when LOST filter is active -->
										<div class="p-4 bg-muted/20">
											<div class="flex flex-col sm:flex-row items-start gap-4">
												{#if group.lostItem.image_url}
													<button
														type="button"
														class="relative w-full sm:w-32 h-48 sm:h-32 bg-muted overflow-hidden rounded-md flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group flex-shrink-0"
														onclick={(e) => openImageModal(getImageUrl(group.lostItem.image_url!), group.lostItem.description, e)}
													>
														<img
															src={getImageUrl(group.lostItem.image_url)}
															alt={group.lostItem.description}
															class="w-full h-full object-cover"
														/>
														<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
															<ZoomIn class="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
														</div>
													</button>
												{:else}
													<div class="w-full sm:w-32 h-48 sm:h-32 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
														<Package class="h-8 w-8 text-muted-foreground" />
													</div>
												{/if}
												<div class="flex-1 min-w-0 w-full space-y-2">
													<div>
														<p class="font-medium break-words text-base">{group.lostItem.description}</p>
														<p class="text-sm text-muted-foreground mt-1">
															<strong>Location:</strong> {group.lostItem.location}
														</p>
													</div>
													<div class="flex flex-wrap gap-2">
														<Badge variant="destructive">LOST</Badge>
														{#if !group.lostItem.is_active}
															<Badge variant="secondary">Archived</Badge>
														{:else}
															<Badge variant="outline">Active</Badge>
														{/if}
														{#if group.lostItem.is_admin_report}
															<Badge variant="outline">Admin Report</Badge>
														{/if}
													</div>
													<div class="text-xs text-muted-foreground space-y-1">
														<p>
															<strong>Reported by:</strong> {group.lostItem.reported_by.name} ({group.lostItem.reported_by.email})
														</p>
														<p>
															<strong>Contact:</strong> {group.lostItem.reported_by.contact_number}
														</p>
														<p>
															<strong>Reported at:</strong> {formatDate(group.lostItem.reported_at)}
														</p>
														<p class="font-mono text-[10px]">
															ID: {group.lostItem.id}
														</p>
													</div>
												</div>
											</div>
										</div>
									{:else if statusFilter === 'FOUND'}
										<!-- Show only Found Item when FOUND filter is active -->
										<div class="p-4">
											<div class="flex flex-col sm:flex-row items-start gap-4">
												{#if group.foundItem.image_url}
													<button
														type="button"
														class="relative w-full sm:w-32 h-48 sm:h-32 bg-muted overflow-hidden rounded-md flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group flex-shrink-0"
														onclick={(e) => openImageModal(getImageUrl(group.foundItem.image_url!), group.foundItem.description, e)}
													>
														<img
															src={getImageUrl(group.foundItem.image_url)}
															alt={group.foundItem.description}
															class="w-full h-full object-cover"
														/>
														<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
															<ZoomIn class="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
														</div>
													</button>
												{:else}
													<div class="w-full sm:w-32 h-48 sm:h-32 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
														<Package class="h-8 w-8 text-muted-foreground" />
													</div>
												{/if}
												<div class="flex-1 min-w-0 w-full space-y-2">
													<div>
														<p class="font-medium break-words text-base">{group.foundItem.description}</p>
														<p class="text-sm text-muted-foreground mt-1">
															<strong>Location:</strong> {group.foundItem.location}
														</p>
													</div>
													<div class="flex flex-wrap gap-2">
														<Badge variant="default">FOUND</Badge>
														{#if !group.foundItem.is_active}
															<Badge variant="secondary">Archived</Badge>
														{:else}
															<Badge variant="outline">Active</Badge>
														{/if}
														{#if group.foundItem.is_admin_report}
															<Badge variant="outline">Admin Report</Badge>
														{/if}
													</div>
													<div class="text-xs text-muted-foreground space-y-1">
														<p>
															<strong>Reported by:</strong> {group.foundItem.reported_by.name} ({group.foundItem.reported_by.email})
														</p>
														<p>
															<strong>Contact:</strong> {group.foundItem.reported_by.contact_number}
														</p>
														<p>
															<strong>Reported at:</strong> {formatDate(group.foundItem.reported_at)}
														</p>
														<p class="font-mono text-[10px]">
															ID: {group.foundItem.id}
														</p>
													</div>
												</div>
											</div>
										</div>
									{:else}
										<!-- Show both items when no status filter is active -->
										<div class="divide-y">
											<!-- Lost Item -->
											<div class="p-4 bg-muted/20">
												<div class="flex flex-col sm:flex-row items-start gap-4">
													{#if group.lostItem.image_url}
														<button
															type="button"
															class="relative w-full sm:w-32 h-48 sm:h-32 bg-muted overflow-hidden rounded-md flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group flex-shrink-0"
															onclick={(e) => openImageModal(getImageUrl(group.lostItem.image_url!), group.lostItem.description, e)}
														>
															<img
																src={getImageUrl(group.lostItem.image_url)}
																alt={group.lostItem.description}
																class="w-full h-full object-cover"
															/>
															<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
																<ZoomIn class="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
															</div>
														</button>
													{:else}
														<div class="w-full sm:w-32 h-48 sm:h-32 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
															<Package class="h-8 w-8 text-muted-foreground" />
														</div>
													{/if}
													<div class="flex-1 min-w-0 w-full space-y-2">
														<div>
															<p class="font-medium break-words text-base">{group.lostItem.description}</p>
															<p class="text-sm text-muted-foreground mt-1">
																<strong>Location:</strong> {group.lostItem.location}
															</p>
														</div>
														<div class="flex flex-wrap gap-2">
															<Badge variant="destructive">LOST</Badge>
															{#if !group.lostItem.is_active}
																<Badge variant="secondary">Archived</Badge>
															{:else}
																<Badge variant="outline">Active</Badge>
															{/if}
															{#if group.lostItem.is_admin_report}
																<Badge variant="outline">Admin Report</Badge>
															{/if}
														</div>
														<div class="text-xs text-muted-foreground space-y-1">
															<p>
																<strong>Reported by:</strong> {group.lostItem.reported_by.name} ({group.lostItem.reported_by.email})
															</p>
															<p>
																<strong>Contact:</strong> {group.lostItem.reported_by.contact_number}
															</p>
															<p>
																<strong>Reported at:</strong> {formatDate(group.lostItem.reported_at)}
															</p>
															<p class="font-mono text-[10px]">
																ID: {group.lostItem.id}
															</p>
														</div>
													</div>
												</div>
											</div>
											
											<!-- Found Item -->
											<div class="p-4">
												<div class="flex flex-col sm:flex-row items-start gap-4">
													{#if group.foundItem.image_url}
														<button
															type="button"
															class="relative w-full sm:w-32 h-48 sm:h-32 bg-muted overflow-hidden rounded-md flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group flex-shrink-0"
															onclick={(e) => openImageModal(getImageUrl(group.foundItem.image_url!), group.foundItem.description, e)}
														>
															<img
																src={getImageUrl(group.foundItem.image_url)}
																alt={group.foundItem.description}
																class="w-full h-full object-cover"
															/>
															<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
																<ZoomIn class="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
															</div>
														</button>
													{:else}
														<div class="w-full sm:w-32 h-48 sm:h-32 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
															<Package class="h-8 w-8 text-muted-foreground" />
														</div>
													{/if}
													<div class="flex-1 min-w-0 w-full space-y-2">
														<div>
															<p class="font-medium break-words text-base">{group.foundItem.description}</p>
															<p class="text-sm text-muted-foreground mt-1">
																<strong>Location:</strong> {group.foundItem.location}
															</p>
														</div>
														<div class="flex flex-wrap gap-2">
															<Badge variant="default">FOUND</Badge>
															{#if !group.foundItem.is_active}
																<Badge variant="secondary">Archived</Badge>
															{:else}
																<Badge variant="outline">Active</Badge>
															{/if}
															{#if group.foundItem.is_admin_report}
																<Badge variant="outline">Admin Report</Badge>
															{/if}
														</div>
														<div class="text-xs text-muted-foreground space-y-1">
															<p>
																<strong>Reported by:</strong> {group.foundItem.reported_by.name} ({group.foundItem.reported_by.email})
															</p>
															<p>
																<strong>Contact:</strong> {group.foundItem.reported_by.contact_number}
															</p>
															<p>
																<strong>Reported at:</strong> {formatDate(group.foundItem.reported_at)}
															</p>
															<p class="font-mono text-[10px]">
																ID: {group.foundItem.id}
															</p>
														</div>
													</div>
												</div>
											</div>
										</div>
									{/if}
								</div>
							{/if}
						</div>
					{:else}
						<!-- Single Item -->
						<div class="flex flex-col sm:flex-row items-start gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors">
							{#if group.item.image_url}
								<button
									type="button"
									class="relative w-full sm:w-32 h-48 sm:h-32 bg-muted overflow-hidden rounded-md flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group flex-shrink-0"
									onclick={(e) => openImageModal(getImageUrl(group.item.image_url!), group.item.description, e)}
								>
									<img
										src={getImageUrl(group.item.image_url)}
										alt={group.item.description}
										class="w-full h-full object-cover"
									/>
									<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
										<ZoomIn class="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
									</div>
								</button>
							{:else}
								<div class="w-full sm:w-32 h-48 sm:h-32 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
									<Package class="h-8 w-8 text-muted-foreground" />
								</div>
							{/if}
							<div class="flex-1 min-w-0 w-full space-y-2">
								<div>
									<p class="font-medium break-words text-base">{group.item.description}</p>
									<p class="text-sm text-muted-foreground mt-1">
										<strong>Location:</strong> {group.item.location}
									</p>
								</div>
								<div class="flex flex-wrap gap-2">
									<Badge variant={group.item.status === 'LOST' ? 'destructive' : 'default'}>
										{group.item.status}
									</Badge>
									{#if !group.item.is_active}
										<Badge variant="secondary">Archived</Badge>
									{:else}
										<Badge variant="outline">Active</Badge>
									{/if}
									{#if group.item.is_admin_report}
										<Badge variant="outline">Admin Report</Badge>
									{/if}
								</div>
								<div class="text-xs text-muted-foreground space-y-1">
									<p>
										<strong>Reported by:</strong> {group.item.reported_by.name} ({group.item.reported_by.email})
									</p>
									<p>
										<strong>Contact:</strong> {group.item.reported_by.contact_number}
									</p>
									<p>
										<strong>Reported at:</strong> {formatDate(group.item.reported_at)}
									</p>
									<p class="font-mono text-[10px]">
										ID: {group.item.id}
									</p>
								</div>
							</div>
						</div>
					{/if}
				{/each}
			</div>
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

