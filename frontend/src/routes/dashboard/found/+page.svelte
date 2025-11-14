<script lang="ts">
	import { Card, CardContent } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { getAllFoundItems, searchItems } from '$lib/api/items';
	import { getImageUrl } from '$lib/api/config';
	import { onMount } from 'svelte';
	import type { Item } from '$lib/api/items';
	import { Search, Package, MapPin, Calendar, ZoomIn } from "@lucide/svelte";
	import { toast } from 'svelte-sonner';

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
	let searchQuery = $state('');
	let locationFilter = $state<string>('');
	let selectedItem = $state<Item | null>(null);
	let dialogOpen = $state(false);
	let imageModalOpen = $state(false);
	let selectedImageUrl = $state<string | null>(null);
	let selectedImageAlt = $state<string>('');

	onMount(async () => {
		await loadItems();
	});

	async function loadItems() {
		loading = true;
		try {
			if (searchQuery.length >= 2) {
				items = await searchItems({ q: searchQuery, status: 'FOUND' });
			} else {
				items = await getAllFoundItems(
					locationFilter ? { location: locationFilter } : undefined
				);
			}
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

	function openItemDetails(item: Item) {
		selectedItem = item;
		dialogOpen = true;
	}

	function openImageModal(imageUrl: string, alt: string, event?: MouseEvent) {
		if (event) {
			event.stopPropagation();
		}
		selectedImageUrl = imageUrl;
		selectedImageAlt = alt;
		imageModalOpen = true;
	}

	let searchTimeout: ReturnType<typeof setTimeout>;
	$effect(() => {
		clearTimeout(searchTimeout);
		if (searchQuery.length >= 2 || searchQuery.length === 0) {
			searchTimeout = setTimeout(() => {
				loadItems();
			}, 500);
		}
	});
</script>

<div class="space-y-4 sm:space-y-6 md:space-y-8">
	<div class="space-y-1 sm:space-y-2">
		<h1 class="text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight">Browse Found Items</h1>
		<p class="text-muted-foreground text-sm sm:text-base md:text-lg">Search and browse items that have been found</p>
	</div>

	<div class="flex flex-col sm:flex-row gap-4">
		<div class="flex-1 relative">
			<Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
			<Input
				type="text"
				placeholder="Search items (min 2 characters)..."
				bind:value={searchQuery}
				class="pl-10"
			/>
		</div>
		<Select
			type="single"
			bind:value={locationFilter}
			onValueChange={() => {
				loadItems();
			}}
		>
			<SelectTrigger class="w-full sm:w-[200px]">
				{locationFilter || 'Filter by location'}
			</SelectTrigger>
			<SelectContent>
				<SelectItem value="">All Locations</SelectItem>
				{#each LOCATIONS as loc}
					<SelectItem value={loc}>{loc}</SelectItem>
				{/each}
			</SelectContent>
		</Select>
	</div>

	{#if loading}
		<div class="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
			{#each Array(6) as _}
				<Card>
					<CardContent class="p-0">
						<Skeleton class="w-full h-48 rounded-t-lg" />
						<div class="p-4 space-y-2">
							<Skeleton class="h-4 w-full" />
							<Skeleton class="h-3 w-3/4" />
							<Skeleton class="h-3 w-1/2" />
							<div class="flex items-center justify-between pt-2">
								<Skeleton class="h-6 w-16 rounded-full" />
								<Skeleton class="h-6 w-20 rounded-full" />
							</div>
						</div>
					</CardContent>
				</Card>
			{/each}
		</div>
	{:else if items.length === 0}
		<Card>
			<CardContent class="py-20 text-center">
				<div class="inline-flex items-center justify-center w-24 h-24 rounded-full bg-muted mb-6">
					<Package class="h-12 w-12 text-muted-foreground" />
				</div>
				<p class="text-muted-foreground font-semibold text-xl mb-2">No items found</p>
				<p class="text-sm text-muted-foreground">
					{searchQuery || locationFilter
						? 'Try adjusting your search or filter criteria.'
						: 'No found items have been reported yet.'}
				</p>
			</CardContent>
		</Card>
	{:else}
		<div class="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
			{#each items as item}
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
									onclick={(e) => openImageModal(getImageUrl(item.image_url), item.description, e)}
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
						<div class="px-4 pb-4 pt-3 space-y-2">
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
								<Badge variant="secondary">{item.status}</Badge>
								{#if item.similarity_score}
									<Badge variant="outline">
										{(item.similarity_score * 100).toFixed(0)}% match
									</Badge>
								{/if}
							</div>
						</div>
					</CardContent>
				</Card>
			{/each}
		</div>
	{/if}

	<Dialog.Root bind:open={dialogOpen}>
		<Dialog.Content class="max-w-3xl max-h-[90vh] overflow-y-auto">
			{#if selectedItem}
				<Dialog.Header>
					<Dialog.Title>Found Item Details</Dialog.Title>
					<Dialog.Description>
						Complete information about this found item. Contact information will be shared if you report a matching lost item and the match is approved.
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

						{#if selectedItem.similarity_score}
							<div>
								<p class="text-sm font-medium text-muted-foreground mb-2">Match Score</p>
								<Badge variant="outline" class="text-lg">
									{(selectedItem.similarity_score * 100).toFixed(0)}% match
								</Badge>
								<p class="text-xs text-muted-foreground mt-2">
									This score indicates how similar this item is to your reported lost items.
								</p>
							</div>
						{/if}

						<div class="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-md border border-blue-200 dark:border-blue-800">
							<p class="text-xs text-blue-700 dark:text-blue-300">
								<strong>Privacy Note:</strong> Contact information of the person who found this item will only be shared with you if you report a matching lost item and they approve the match.
							</p>
						</div>
					</div>
				</div>

				<Dialog.Footer>
					<Button
						variant="outline"
						onclick={() => (dialogOpen = false)}
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

