<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { Tabs, TabsContent, TabsList, TabsTrigger } from '$lib/components/ui/tabs';
	import * as Dialog from '$lib/components/ui/dialog';
	import { getItems } from '$lib/api/admin';
	import { resolveItem, deleteItem } from '$lib/api/items';
	import { getImageUrl } from '$lib/api/config';
	import { onMount } from 'svelte';
	import type { Item } from '$lib/api/items';
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
	import { Package, MapPin, Calendar, CheckCircle, Trash2, Archive, AlertCircle, Search, X, Eye, ZoomIn, Filter, Shield } from '@lucide/svelte';
	import { toast } from 'svelte-sonner';
	import { Skeleton } from '$lib/components/ui/skeleton';

	const LOCATIONS = [
		'Cafeteria',
		'Library',
		'Hostel A',
		'Hostel B',
		'Hostel C',
		'Tan Block',
		'Cos Block',
		'G Block',
		'B Block'
	];

	let items = $state<Item[]>([]);
	let loading = $state(false);
	let activeTab = $state<'all' | 'lost' | 'found' | 'archived'>('all');
	let selectedItem = $state<Item | null>(null);
	let resolveDialogOpen = $state(false);
	let deleteDialogOpen = $state(false);
	let detailDialogOpen = $state(false);
	let actionLoading = $state(false);
	let searchQuery = $state('');
	let locationFilter = $state<string>('');
	let imageModalOpen = $state(false);
	let selectedImageUrl = $state<string | null>(null);
	let selectedImageAlt = $state<string>('');

	onMount(async () => {
		await loadItems();
	});

	async function loadItems() {
		loading = true;
		try {
			const includeArchived = activeTab === 'archived';
			const statusFilter = activeTab === 'lost' ? 'LOST' : activeTab === 'found' ? 'FOUND' : undefined;
			const allItems = await getItems({
				status: statusFilter,
				include_archived: includeArchived,
				limit: 200
			});
			// Filter only admin-reported items
			items = allItems.filter(item => item.is_admin_report);
		} catch (err) {
			console.error('Failed to load items:', err);
			toast.error('Failed to load items. Please try again.');
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

	let successMessage = $state<string | null>(null);
	let errorMessage = $state<string | null>(null);

	async function handleResolve() {
		if (!selectedItem || selectedItem.status !== 'LOST') {
			errorMessage = 'Only lost items can be resolved. Found items are automatically archived when matches are approved.';
			setTimeout(() => errorMessage = null, 5000);
			return;
		}
		actionLoading = true;
		errorMessage = null;
		successMessage = null;
		try {
			await resolveItem(selectedItem.id);
			successMessage = 'Item resolved successfully.';
			toast.success('Item resolved', {
				description: 'The item has been marked as resolved.'
			});
			await loadItems();
			resolveDialogOpen = false;
			selectedItem = null;
			setTimeout(() => successMessage = null, 3000);
		} catch (err) {
			const errMsg = err instanceof Error ? err.message : 'Failed to resolve item';
			errorMessage = errMsg;
			toast.error('Failed to resolve item', {
				description: errMsg
			});
			setTimeout(() => errorMessage = null, 5000);
		} finally {
			actionLoading = false;
		}
	}

	async function handleDelete() {
		if (!selectedItem) return;
		actionLoading = true;
		errorMessage = null;
		successMessage = null;
		try {
			await deleteItem(selectedItem.id);
			successMessage = 'Item deleted successfully.';
			toast.success('Item deleted', {
				description: 'The item has been deleted successfully.'
			});
			await loadItems();
			deleteDialogOpen = false;
			selectedItem = null;
			setTimeout(() => successMessage = null, 3000);
		} catch (err) {
			const errMsg = err instanceof Error ? err.message : 'Failed to delete item';
			errorMessage = errMsg;
			toast.error('Failed to delete item', {
				description: errMsg
			});
			setTimeout(() => errorMessage = null, 5000);
		} finally {
			actionLoading = false;
		}
	}

	function openResolveDialog(item: Item) {
		selectedItem = item;
		resolveDialogOpen = true;
	}

	function openDeleteDialog(item: Item) {
		selectedItem = item;
		deleteDialogOpen = true;
	}

	// Filter items based on search and location
	let filteredItems = $derived.by(() => {
		let result = items;
		
		// Apply search filter
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase().trim();
			result = result.filter(item => 
				item.description.toLowerCase().includes(query) ||
				item.location.toLowerCase().includes(query)
			);
		}
		
		// Apply location filter
		if (locationFilter) {
			result = result.filter(item => item.location === locationFilter);
		}
		
		return result;
	});

	let lostItems = $derived(filteredItems.filter((item) => item.status === 'LOST' && item.is_active));
	let foundItems = $derived(filteredItems.filter((item) => item.status === 'FOUND' && item.is_active));
	let archivedItems = $derived(filteredItems.filter((item) => !item.is_active));
	let allActiveItems = $derived(filteredItems.filter((item) => item.is_active));

	function openItemDetails(item: Item) {
		selectedItem = item;
		detailDialogOpen = true;
	}

	function openImageModal(imageUrl: string, alt: string, event?: MouseEvent) {
		if (event) {
			event.stopPropagation();
		}
		selectedImageUrl = imageUrl;
		selectedImageAlt = alt;
		imageModalOpen = true;
	}

	function clearSearch() {
		searchQuery = '';
	}
</script>

<div class="space-y-6">
	<div class="flex items-center gap-2">
		<Shield class="h-5 w-5 text-primary" />
		<div>
			<h2 class="text-2xl font-bold tracking-tight">My Admin Reports</h2>
			<p class="text-muted-foreground text-sm">Manage items reported by admin office</p>
		</div>
	</div>

	<!-- Search and Filters -->
	<div class="flex flex-col sm:flex-row gap-2 sm:gap-3">
		<div class="relative flex-1">
			<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
			<Input
				type="text"
				placeholder="Search by description or location..."
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
		<Select
			type="single"
			bind:value={locationFilter}
		>
			<SelectTrigger class="w-full sm:w-[200px] text-sm">
				<Filter class="h-4 w-4 mr-2" />
				{locationFilter || 'All Locations'}
			</SelectTrigger>
			<SelectContent>
				<SelectItem value="">All Locations</SelectItem>
				{#each LOCATIONS as loc}
					<SelectItem value={loc}>{loc}</SelectItem>
				{/each}
			</SelectContent>
		</Select>
	</div>

	{#if successMessage}
		<div class="flex items-center gap-2 p-3 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30 rounded-md border border-green-200 dark:border-green-800">
			<CheckCircle class="h-4 w-4" />
			<span>{successMessage}</span>
		</div>
	{/if}

	{#if errorMessage}
		<div class="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md border border-destructive/20">
			<AlertCircle class="h-4 w-4" />
			<span>{errorMessage}</span>
		</div>
	{/if}

	<Tabs bind:value={activeTab} onValueChange={loadItems}>
		<TabsList class="grid w-full grid-cols-4 gap-1 sm:gap-2 overflow-x-auto">
			<TabsTrigger value="all" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation">All</TabsTrigger>
			<TabsTrigger value="lost" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation">Lost</TabsTrigger>
			<TabsTrigger value="found" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation">Found</TabsTrigger>
			<TabsTrigger value="archived" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation">Archived</TabsTrigger>
		</TabsList>

		<TabsContent value="all" class="space-y-4 mt-4">
			{#if loading}
				<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each Array(6) as _}
						<Card>
							<CardContent class="p-0">
								<Skeleton class="w-full h-48 rounded-t-lg" />
								<div class="p-4 space-y-2">
									<Skeleton class="h-4 w-full" />
									<Skeleton class="h-3 w-3/4" />
									<Skeleton class="h-3 w-1/2" />
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{:else if allActiveItems.length === 0}
				<Card>
					<CardContent class="py-16 text-center">
						<Shield class="h-16 w-16 text-muted-foreground mx-auto mb-4 opacity-50" />
						<p class="text-muted-foreground font-medium text-lg mb-1">No admin-reported items</p>
						<p class="text-sm text-muted-foreground">Start by reporting items in the Report Items tab</p>
					</CardContent>
				</Card>
			{:else}
				<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each allActiveItems as item}
						<Card
							class="cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200 border-2 hover:border-primary/20"
							onclick={() => openItemDetails(item)}
						>
							<CardContent class="p-0">
								<div class="px-4 pt-4">
									{#if item.image_url}
										<button
											type="button"
											class="relative w-full h-48 bg-muted overflow-hidden rounded-xl flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
											onclick={(e) => openImageModal(getImageUrl(item.image_url!), item.description, e)}
										>
											<img
												src={getImageUrl(item.image_url)}
												alt={item.description}
												class="max-w-full max-h-full object-contain"
											/>
											<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
												<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
											</div>
										</button>
									{:else}
										<div class="w-full h-48 bg-muted rounded-xl flex items-center justify-center">
											<Package class="h-12 w-12 text-muted-foreground" />
										</div>
									{/if}
								</div>
								<div class="p-4 space-y-2">
									<p class="font-medium line-clamp-2">{item.description}</p>
									<div class="flex items-center gap-2 text-sm text-muted-foreground">
										<MapPin class="h-4 w-4" />
										<span>{item.location}</span>
									</div>
									<div class="flex items-center gap-2 text-sm text-muted-foreground">
										<Calendar class="h-4 w-4" />
										<span>{formatDate(item.reported_at)}</span>
									</div>
									<div class="flex items-center justify-between pt-2">
										<Badge variant={item.status === 'LOST' ? 'destructive' : 'default'}>
											{item.status}
										</Badge>
										<div class="flex gap-2">
											<Badge variant="outline" class="bg-primary/10 text-primary border-primary/20">
												<Shield class="h-3 w-3 mr-1 inline" />
												Admin
											</Badge>
											{#if item.has_match_found}
												<Badge variant="default" class="bg-green-600">Match Found</Badge>
											{/if}
										</div>
									</div>
									<div class="flex gap-2 pt-2">
										<Button
											variant="outline"
											size="sm"
											class="flex-1"
											onclick={(e) => {
												e.stopPropagation();
												openItemDetails(item);
											}}
										>
											<Eye class="h-4 w-4 mr-2" />
											View Details
										</Button>
										{#if item.status === 'LOST' && item.is_active}
											<Button
												variant="outline"
												size="sm"
												onclick={(e) => {
													e.stopPropagation();
													openResolveDialog(item);
												}}
											>
												<CheckCircle class="h-4 w-4" />
											</Button>
										{/if}
										<Button
											variant="outline"
											size="sm"
											onclick={(e) => {
												e.stopPropagation();
												openDeleteDialog(item);
											}}
										>
											<Trash2 class="h-4 w-4" />
										</Button>
									</div>
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{/if}
		</TabsContent>

		<TabsContent value="lost" class="space-y-4 mt-4">
			{#if loading}
				<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each Array(3) as _}
						<Card>
							<CardContent class="p-0">
								<Skeleton class="w-full h-48 rounded-t-lg" />
								<div class="p-4 space-y-2">
									<Skeleton class="h-4 w-full" />
									<Skeleton class="h-3 w-3/4" />
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{:else if lostItems.length === 0}
				<Card>
					<CardContent class="py-16 text-center">
						<Package class="h-16 w-16 text-muted-foreground mx-auto mb-4 opacity-50" />
						<p class="text-muted-foreground font-medium text-lg mb-1">No lost items</p>
						<p class="text-sm text-muted-foreground">Report a lost item to get started</p>
					</CardContent>
				</Card>
			{:else}
				<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each lostItems as item}
						<Card
							class="cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200 border-2 hover:border-primary/20"
							onclick={() => openItemDetails(item)}
						>
							<CardContent class="p-0">
								<div class="px-4 pt-4">
									{#if item.image_url}
										<button
											type="button"
											class="relative w-full h-48 bg-muted overflow-hidden rounded-xl flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
											onclick={(e) => openImageModal(getImageUrl(item.image_url!), item.description, e)}
										>
											<img
												src={getImageUrl(item.image_url)}
												alt={item.description}
												class="max-w-full max-h-full object-contain"
											/>
											<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
												<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
											</div>
										</button>
									{:else}
										<div class="w-full h-48 bg-muted rounded-xl flex items-center justify-center">
											<Package class="h-12 w-12 text-muted-foreground" />
										</div>
									{/if}
								</div>
								<div class="p-4 space-y-2">
									<p class="font-medium line-clamp-2">{item.description}</p>
									<div class="flex items-center gap-2 text-sm text-muted-foreground">
										<MapPin class="h-4 w-4" />
										<span>{item.location}</span>
									</div>
									<div class="flex items-center gap-2 text-sm text-muted-foreground">
										<Calendar class="h-4 w-4" />
										<span>{formatDate(item.reported_at)}</span>
									</div>
									<div class="flex items-center justify-between pt-2">
										<Badge variant="destructive">LOST</Badge>
										<div class="flex gap-2">
											<Badge variant="outline" class="bg-primary/10 text-primary border-primary/20">
												<Shield class="h-3 w-3 mr-1 inline" />
												Admin
											</Badge>
											{#if item.has_match_found}
												<Badge variant="default" class="bg-green-600">Match Found</Badge>
											{/if}
										</div>
									</div>
									<div class="flex gap-2 pt-2">
										<Button
											variant="outline"
											size="sm"
											class="flex-1"
											onclick={(e) => {
												e.stopPropagation();
												openItemDetails(item);
											}}
										>
											<Eye class="h-4 w-4 mr-2" />
											View Details
										</Button>
										{#if item.is_active}
											<Button
												variant="outline"
												size="sm"
												onclick={(e) => {
													e.stopPropagation();
													openResolveDialog(item);
												}}
											>
												<CheckCircle class="h-4 w-4" />
											</Button>
										{/if}
										<Button
											variant="outline"
											size="sm"
											onclick={(e) => {
												e.stopPropagation();
												openDeleteDialog(item);
											}}
										>
											<Trash2 class="h-4 w-4" />
										</Button>
									</div>
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{/if}
		</TabsContent>

		<TabsContent value="found" class="space-y-4 mt-4">
			{#if loading}
				<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each Array(3) as _}
						<Card>
							<CardContent class="p-0">
								<Skeleton class="w-full h-48 rounded-t-lg" />
								<div class="p-4 space-y-2">
									<Skeleton class="h-4 w-full" />
									<Skeleton class="h-3 w-3/4" />
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{:else if foundItems.length === 0}
				<Card>
					<CardContent class="py-16 text-center">
						<Package class="h-16 w-16 text-muted-foreground mx-auto mb-4 opacity-50" />
						<p class="text-muted-foreground font-medium text-lg mb-1">No found items</p>
						<p class="text-sm text-muted-foreground">Report a found item to help others</p>
					</CardContent>
				</Card>
			{:else}
				<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each foundItems as item}
						<Card
							class="cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200 border-2 hover:border-primary/20"
							onclick={() => openItemDetails(item)}
						>
							<CardContent class="p-0">
								<div class="px-4 pt-4">
									{#if item.image_url}
										<button
											type="button"
											class="relative w-full h-48 bg-muted overflow-hidden rounded-xl flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
											onclick={(e) => openImageModal(getImageUrl(item.image_url!), item.description, e)}
										>
											<img
												src={getImageUrl(item.image_url)}
												alt={item.description}
												class="max-w-full max-h-full object-contain"
											/>
											<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
												<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
											</div>
										</button>
									{:else}
										<div class="w-full h-48 bg-muted rounded-xl flex items-center justify-center">
											<Package class="h-12 w-12 text-muted-foreground" />
										</div>
									{/if}
								</div>
								<div class="p-4 space-y-2">
									<p class="font-medium line-clamp-2">{item.description}</p>
									<div class="flex items-center gap-2 text-sm text-muted-foreground">
										<MapPin class="h-4 w-4" />
										<span>{item.location}</span>
									</div>
									<div class="flex items-center gap-2 text-sm text-muted-foreground">
										<Calendar class="h-4 w-4" />
										<span>{formatDate(item.reported_at)}</span>
									</div>
									<div class="flex items-center justify-between pt-2">
										<Badge variant="default">FOUND</Badge>
										<div class="flex gap-2">
											<Badge variant="outline" class="bg-primary/10 text-primary border-primary/20">
												<Shield class="h-3 w-3 mr-1 inline" />
												Admin
											</Badge>
											{#if item.has_match_found}
												<Badge variant="default" class="bg-green-600">Match Found</Badge>
											{/if}
										</div>
									</div>
									<div class="flex gap-2 pt-2">
										<Button
											variant="outline"
											size="sm"
											class="flex-1"
											onclick={(e) => {
												e.stopPropagation();
												openItemDetails(item);
											}}
										>
											<Eye class="h-4 w-4 mr-2" />
											View Details
										</Button>
										{#if item.is_active}
											<Button
												variant="outline"
												size="sm"
												onclick={(e) => {
													e.stopPropagation();
													openDeleteDialog(item);
												}}
											>
												<Trash2 class="h-4 w-4" />
											</Button>
										{/if}
									</div>
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{/if}
		</TabsContent>

		<TabsContent value="archived" class="space-y-4 mt-4">
			{#if loading}
				<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each Array(3) as _}
						<Card>
							<CardContent class="p-0">
								<Skeleton class="w-full h-48 rounded-t-lg opacity-50" />
								<div class="p-4 space-y-2">
									<Skeleton class="h-4 w-full" />
									<Skeleton class="h-3 w-3/4" />
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{:else if archivedItems.length === 0}
				<Card>
					<CardContent class="py-16 text-center">
						<Archive class="h-16 w-16 text-muted-foreground mx-auto mb-4 opacity-50" />
						<p class="text-muted-foreground font-medium text-lg mb-1">No archived items</p>
						<p class="text-sm text-muted-foreground">Resolved items will appear here</p>
					</CardContent>
				</Card>
			{:else}
				<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
					{#each archivedItems as item}
						<Card
							class="cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200 border-2 hover:border-primary/20 opacity-75"
							onclick={() => openItemDetails(item)}
						>
							<CardContent class="p-0">
								<div class="px-4 pt-4">
									{#if item.image_url}
										<button
											type="button"
											class="relative w-full h-48 bg-muted overflow-hidden rounded-xl flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
											onclick={(e) => openImageModal(getImageUrl(item.image_url!), item.description, e)}
										>
											<img
												src={getImageUrl(item.image_url)}
												alt={item.description}
												class="max-w-full max-h-full object-contain"
											/>
											<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
												<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
											</div>
										</button>
									{:else}
										<div class="w-full h-48 bg-muted rounded-xl flex items-center justify-center">
											<Package class="h-12 w-12 text-muted-foreground" />
										</div>
									{/if}
								</div>
								<div class="p-4 space-y-2">
									<p class="font-medium line-clamp-2">{item.description}</p>
									<div class="flex items-center gap-2 text-sm text-muted-foreground">
										<MapPin class="h-4 w-4" />
										<span>{item.location}</span>
									</div>
									<div class="flex items-center gap-2 text-sm text-muted-foreground">
										<Calendar class="h-4 w-4" />
										<span>{formatDate(item.reported_at)}</span>
									</div>
									<div class="flex items-center justify-between pt-2">
										<Badge variant={item.status === 'LOST' ? 'destructive' : 'default'}>
											{item.status}
										</Badge>
										<div class="flex gap-2">
											<Badge variant="outline" class="bg-primary/10 text-primary border-primary/20">
												<Shield class="h-3 w-3 mr-1 inline" />
												Admin
											</Badge>
											{#if item.has_match_found}
												<Badge variant="default" class="bg-green-600">Match Found</Badge>
											{/if}
											<Badge variant="secondary">Archived</Badge>
										</div>
									</div>
									<div class="flex gap-2 pt-2 items-center">
										<Button
											variant="outline"
											size="sm"
											class="flex-1"
											onclick={(e) => {
												e.stopPropagation();
												openItemDetails(item);
											}}
										>
											<Eye class="h-4 w-4 mr-2" />
											View Details
										</Button>
										<Button
											variant="outline"
											size="icon"
											class="h-9 w-9"
											onclick={(e) => {
												e.stopPropagation();
												openDeleteDialog(item);
											}}
										>
											<Trash2 class="h-4 w-4" />
										</Button>
									</div>
								</div>
							</CardContent>
						</Card>
					{/each}
				</div>
			{/if}
		</TabsContent>
	</Tabs>

	<AlertDialog bind:open={resolveDialogOpen}>
		<AlertDialogContent>
			<AlertDialogHeader>
				<AlertDialogTitle>Resolve Lost Item?</AlertDialogTitle>
				<AlertDialogDescription>
					Are you sure you want to mark this item as resolved? This will archive it and remove it from active matching. Found items are automatically archived when matches are approved.
				</AlertDialogDescription>
			</AlertDialogHeader>
			<AlertDialogFooter>
				<AlertDialogCancel disabled={actionLoading}>Cancel</AlertDialogCancel>
				<AlertDialogAction onclick={handleResolve} disabled={actionLoading}>
					{actionLoading ? 'Processing...' : 'Resolve'}
				</AlertDialogAction>
			</AlertDialogFooter>
		</AlertDialogContent>
	</AlertDialog>

	<AlertDialog bind:open={deleteDialogOpen}>
		<AlertDialogContent>
			<AlertDialogHeader>
				<AlertDialogTitle>Delete Item?</AlertDialogTitle>
				<AlertDialogDescription>
					Are you sure you want to delete this item? This action cannot be undone. Items with approved matches cannot be deleted.
				</AlertDialogDescription>
			</AlertDialogHeader>
			<AlertDialogFooter>
				<AlertDialogCancel disabled={actionLoading}>Cancel</AlertDialogCancel>
				<AlertDialogAction
					onclick={handleDelete}
					disabled={actionLoading}
					class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
				>
					{actionLoading ? 'Deleting...' : 'Delete'}
				</AlertDialogAction>
			</AlertDialogFooter>
		</AlertDialogContent>
	</AlertDialog>

	<!-- Item Details Modal -->
	<Dialog.Root bind:open={detailDialogOpen}>
		<Dialog.Content class="max-w-3xl max-h-[90vh] overflow-y-auto">
			{#if selectedItem}
				<Dialog.Header>
					<Dialog.Title>Item Details</Dialog.Title>
					<Dialog.Description>
						Complete information about this admin-reported item
					</Dialog.Description>
				</Dialog.Header>
				
				<div class="space-y-6 mt-4">
					<!-- Image -->
					{#if selectedItem.image_url}
						<button
							type="button"
							class="relative w-full h-64 bg-muted overflow-hidden rounded-lg flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity group"
							onclick={() => openImageModal(getImageUrl(selectedItem.image_url!), selectedItem.description)}
						>
							<img
								src={getImageUrl(selectedItem.image_url)}
								alt={selectedItem.description}
								class="max-w-full max-h-full object-contain"
							/>
							<div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
								<ZoomIn class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
							</div>
						</button>
					{:else}
						<div class="w-full h-64 bg-muted rounded-lg flex items-center justify-center">
							<Package class="h-16 w-16 text-muted-foreground" />
						</div>
					{/if}

					<!-- Details -->
					<div class="space-y-4">
						<div>
							<p class="text-sm font-medium text-muted-foreground mb-1">Description</p>
							<p class="text-base">{selectedItem.description}</p>
						</div>
						
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div>
								<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
									<MapPin class="h-4 w-4" />
									Location
								</p>
								<p class="text-base">{selectedItem.location}</p>
							</div>
							<div>
								<p class="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-1">
									<Calendar class="h-4 w-4" />
									Reported At
								</p>
								<p class="text-base">{formatDate(selectedItem.reported_at)}</p>
							</div>
						</div>

						<div>
							<p class="text-sm font-medium text-muted-foreground mb-2">Status</p>
							<div class="flex flex-wrap gap-2">
								<Badge variant={selectedItem.status === 'LOST' ? 'destructive' : 'default'}>
									{selectedItem.status}
								</Badge>
								{#if !selectedItem.is_active}
									<Badge variant="secondary">Archived</Badge>
								{:else}
									<Badge variant="outline">Active</Badge>
								{/if}
								<Badge variant="outline" class="bg-primary/10 text-primary border-primary/20">
									<Shield class="h-3 w-3 mr-1 inline" />
									Admin Report
								</Badge>
								{#if selectedItem.has_match_found}
									<Badge variant="default" class="bg-green-600">Match Found</Badge>
								{/if}
							</div>
						</div>

						<div>
							<p class="text-sm font-medium text-muted-foreground mb-1">Item ID</p>
							<p class="text-xs font-mono text-muted-foreground break-all">{selectedItem.id}</p>
						</div>
					</div>

					<!-- Actions -->
					<div class="flex flex-col sm:flex-row gap-2 pt-4 border-t">
						{#if selectedItem.status === 'LOST' && selectedItem.is_active}
							<Button
								variant="default"
								class="flex-1"
								onclick={() => {
									detailDialogOpen = false;
									openResolveDialog(selectedItem);
								}}
							>
								<CheckCircle class="h-4 w-4 mr-2" />
								Resolve Item
							</Button>
						{/if}
						<Button
							variant="destructive"
							class="flex-1"
							onclick={() => {
								detailDialogOpen = false;
								openDeleteDialog(selectedItem);
							}}
						>
							<Trash2 class="h-4 w-4 mr-2" />
							Delete Item
						</Button>
					</div>
				</div>

				<Dialog.Footer>
					<Button
						variant="outline"
						onclick={() => (detailDialogOpen = false)}
					>
						Close
					</Button>
				</Dialog.Footer>
			{/if}
		</Dialog.Content>
	</Dialog.Root>

	<!-- Image Modal -->
	<Dialog.Root bind:open={imageModalOpen}>
		<Dialog.Content class="max-w-4xl max-h-[90vh] p-0" showCloseButton={true}>
			{#if selectedImageUrl}
				<div class="relative w-full h-full flex items-center justify-center bg-muted p-4">
					<img
						src={selectedImageUrl}
						alt={selectedImageAlt}
						class="max-w-full max-h-[85vh] object-contain rounded-lg"
					/>
				</div>
			{/if}
		</Dialog.Content>
	</Dialog.Root>
</div>

