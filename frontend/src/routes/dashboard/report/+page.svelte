<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { Tabs, TabsContent, TabsList, TabsTrigger } from '$lib/components/ui/tabs';
	import { reportLostItem, reportFoundItem } from '$lib/api/items';
	import { goto } from '$app/navigation';
	import { AlertCircle, Upload, X, CheckCircle2 } from "@lucide/svelte";
	import { Badge } from '$lib/components/ui/badge';
	import { getUserContext } from '$lib/contexts/user.svelte';
	import { toast } from 'svelte-sonner';
	import { Tooltip, TooltipContent, TooltipTrigger } from '$lib/components/ui/tooltip';
	import { Info } from '@lucide/svelte';

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

	let activeTab = $state<'lost' | 'found'>('lost');
	let description = $state('');
	let location = $state('');
	let imageFile = $state<File | null>(null);
	let imagePreview = $state<string | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let success = $state(false);
	let isDragging = $state(false);
	let fileInputLost: HTMLInputElement | null = $state(null);
	let fileInputFound: HTMLInputElement | null = $state(null);
	let matchesFound = $state<number | null>(null);
	
	const userContext = getUserContext();

	function handleImageSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];
		processFile(file);
	}

	function processFile(file: File | null | undefined) {
		if (!file) return;
		
		if (file.size > 5 * 1024 * 1024) {
			error = 'Image size must be less than 5MB';
			return;
		}
		if (!file.type.startsWith('image/')) {
			error = 'Please select an image file';
			return;
		}
		imageFile = file;
		const reader = new FileReader();
		reader.onload = (e) => {
			imagePreview = e.target?.result as string;
		};
		reader.readAsDataURL(file);
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		event.stopPropagation();
		isDragging = true;
	}

	function handleDragLeave(event: DragEvent) {
		event.preventDefault();
		event.stopPropagation();
		isDragging = false;
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		event.stopPropagation();
		isDragging = false;
		
		const file = event.dataTransfer?.files?.[0];
		processFile(file);
	}

	function triggerFileInput(inputId: 'lost' | 'found') {
		const input = inputId === 'lost' ? fileInputLost : fileInputFound;
		input?.click();
	}

	function removeImage() {
		imageFile = null;
		imagePreview = null;
	}

	async function handleSubmit() {
		if (!description || !location) {
			error = 'Please fill in all required fields';
			return;
		}

		if (activeTab === 'found' && !imageFile) {
			error = 'Image is required for found items';
			return;
		}

		loading = true;
		error = null;
		success = false;

		try {
			if (activeTab === 'lost') {
				await reportLostItem({
					description,
					location,
					image: imageFile || undefined
				});
			} else {
				if (!imageFile) {
					error = 'Image is required for found items';
					loading = false;
					return;
				}
				await reportFoundItem({
					description,
					location,
					image: imageFile
				});
			}

			success = true;
			matchesFound = null;
			
			toast.success('Item reported successfully!', {
				description: activeTab === 'lost' ? 'Your lost item has been reported.' : 'Your found item has been reported.'
			});

			// Wait a bit for backend matching to complete, then check for matches
			setTimeout(async () => {
				try {
					await userContext.refreshMatches();
					const newMatchesCount = userContext.matches.length;
					if (newMatchesCount > 0) {
						matchesFound = newMatchesCount;
						toast.info(`Found ${newMatchesCount} potential match${newMatchesCount !== 1 ? 'es' : ''}!`, {
							description: 'Check your matches page to review them.',
							duration: 5000
						});
					}
				} catch (err) {
					console.error('Failed to check matches:', err);
				}
			}, 2000);

			// Redirect after showing success message
			setTimeout(() => {
				goto('/dashboard');
			}, matchesFound !== null && matchesFound > 0 ? 5000 : 3000);
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to report item. Please try again.';
			error = errorMessage;
			toast.error('Failed to report item', {
				description: errorMessage
			});
		} finally {
			loading = false;
		}
	}
</script>

<div class="max-w-2xl mx-auto space-y-8 px-4">
	<div class="space-y-2">
		<h1 class="text-3xl md:text-4xl font-bold tracking-tight">Report Item</h1>
		<p class="text-muted-foreground text-lg">Report a lost or found item</p>
	</div>

	<Card class="shadow-lg border-2">
		<CardHeader>
			<CardTitle class="text-xl">Item Details</CardTitle>
			<CardDescription class="text-base">Provide information about the item</CardDescription>
		</CardHeader>
		<CardContent>
			<Tabs bind:value={activeTab}>
				<TabsList class="grid w-full grid-cols-2">
					<TabsTrigger value="lost">Lost Item</TabsTrigger>
					<TabsTrigger value="found">Found Item</TabsTrigger>
				</TabsList>

				<TabsContent value="lost" class="space-y-4 mt-4">
					{#if error}
						<div class="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
							<AlertCircle class="h-4 w-4" />
							<span>{error}</span>
						</div>
					{/if}

					{#if success}
						<div class="space-y-2">
							<div class="flex items-center gap-2 p-3 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30 rounded-md">
								<CheckCircle2 class="h-4 w-4" />
								<span>Item reported successfully! Checking for matches...</span>
							</div>
							{#if matchesFound !== null && matchesFound > 0}
								<div class="flex items-center gap-2 p-3 text-sm text-primary bg-primary/10 rounded-md">
									<CheckCircle2 class="h-4 w-4" />
									<span>Found {matchesFound} potential match{matchesFound !== 1 ? 'es' : ''}! Check your matches page.</span>
								</div>
							{:else if matchesFound === 0}
								<div class="flex items-center gap-2 p-3 text-sm text-muted-foreground bg-muted rounded-md">
									<AlertCircle class="h-4 w-4" />
									<span>No matches found yet. We'll notify you if any potential matches are found.</span>
								</div>
							{/if}
						</div>
					{/if}

					<div class="space-y-2">
						<Label for="description-lost" class="flex items-center gap-2">
							Description *
							<Tooltip>
								<TooltipTrigger>
									<Info class="h-3 w-3 text-muted-foreground" />
								</TooltipTrigger>
								<TooltipContent>
									<p>Provide a detailed description to help others identify your item</p>
								</TooltipContent>
							</Tooltip>
						</Label>
						<Textarea
							id="description-lost"
							placeholder="Describe the item (e.g., Black leather wallet with ID card)"
							bind:value={description}
							disabled={loading}
							required
							rows={4}
						/>
					</div>

					<div class="space-y-2">
						<Label for="location-lost">Location *</Label>
						<Select
							type="single"
							bind:value={location}
						>
							<SelectTrigger>
								{location || 'Select location'}
							</SelectTrigger>
							<SelectContent>
								{#each LOCATIONS as loc}
									<SelectItem value={loc}>{loc}</SelectItem>
								{/each}
							</SelectContent>
						</Select>
					</div>

					<div class="space-y-2">
						<Label for="image-lost" class="flex items-center gap-2">
							Image (Optional)
							<Tooltip>
								<TooltipTrigger>
									<Info class="h-3 w-3 text-muted-foreground" />
								</TooltipTrigger>
								<TooltipContent>
									<p>Adding an image increases the chance of finding your item</p>
								</TooltipContent>
							</Tooltip>
						</Label>
						{#if imagePreview}
							<div class="relative bg-muted rounded-md overflow-hidden">
								<img src={imagePreview} alt="Preview" class="w-full h-64 object-contain rounded-md" />
								<Button
									type="button"
									variant="destructive"
									size="icon"
									class="absolute top-2 right-2"
									onclick={removeImage}
								>
									<X class="h-4 w-4" />
								</Button>
							</div>
						{:else}
							<div
								class="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer transition-colors {isDragging
									? 'border-primary bg-primary/10'
									: 'border-muted-foreground/25 hover:bg-muted/50'}"
								onclick={() => triggerFileInput('lost')}
								ondragover={handleDragOver}
								ondragleave={handleDragLeave}
								ondrop={handleDrop}
							>
								<Upload class="h-8 w-8 text-muted-foreground mb-2" />
								<span class="text-sm text-muted-foreground">Click to upload or drag and drop</span>
								<input
									bind:this={fileInputLost}
									id="image-input-lost"
									type="file"
									accept="image/*"
									class="hidden"
									onchange={handleImageSelect}
									disabled={loading}
								/>
							</div>
						{/if}
						<p class="text-xs text-muted-foreground">JPEG, PNG, or WebP (max 5MB)</p>
					</div>

					<Button type="button" class="w-full" onclick={handleSubmit} disabled={loading}>
						{loading ? 'Reporting...' : 'Report Lost Item'}
					</Button>
				</TabsContent>

				<TabsContent value="found" class="space-y-4 mt-4">
					{#if error}
						<div class="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
							<AlertCircle class="h-4 w-4" />
							<span>{error}</span>
						</div>
					{/if}

					{#if success}
						<div class="space-y-2">
							<div class="flex items-center gap-2 p-3 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30 rounded-md">
								<CheckCircle2 class="h-4 w-4" />
								<span>Item reported successfully! Checking for matches...</span>
							</div>
							{#if matchesFound !== null && matchesFound > 0}
								<div class="flex items-center gap-2 p-3 text-sm text-primary bg-primary/10 rounded-md">
									<CheckCircle2 class="h-4 w-4" />
									<span>Found {matchesFound} potential match{matchesFound !== 1 ? 'es' : ''}! Check your matches page.</span>
								</div>
							{:else if matchesFound === 0}
								<div class="flex items-center gap-2 p-3 text-sm text-muted-foreground bg-muted rounded-md">
									<AlertCircle class="h-4 w-4" />
									<span>No matches found yet. We'll notify you if any potential matches are found.</span>
								</div>
							{/if}
						</div>
					{/if}

					<div class="space-y-2">
						<Label for="description-found" class="flex items-center gap-2">
							Description *
							<Tooltip>
								<TooltipTrigger>
									<Info class="h-3 w-3 text-muted-foreground" />
								</TooltipTrigger>
								<TooltipContent>
									<p>Describe what you found to help the owner identify it</p>
								</TooltipContent>
							</Tooltip>
						</Label>
						<Textarea
							id="description-found"
							placeholder="Describe the item (e.g., Black wallet found)"
							bind:value={description}
							disabled={loading}
							required
							rows={4}
						/>
					</div>

					<div class="space-y-2">
						<Label for="location-found">Location *</Label>
						<Select
							type="single"
							bind:value={location}
						>
							<SelectTrigger>
								{location || 'Select location'}
							</SelectTrigger>
							<SelectContent>
								{#each LOCATIONS as loc}
									<SelectItem value={loc}>{loc}</SelectItem>
								{/each}
							</SelectContent>
						</Select>
					</div>

					<div class="space-y-2">
						<Label for="image-found" class="flex items-center gap-2">
							Image *
							<Tooltip>
								<TooltipTrigger>
									<Info class="h-3 w-3 text-muted-foreground" />
								</TooltipTrigger>
								<TooltipContent>
									<p>Image is required for found items to help verify matches</p>
								</TooltipContent>
							</Tooltip>
						</Label>
						{#if imagePreview}
							<div class="relative bg-muted rounded-md overflow-hidden">
								<img src={imagePreview} alt="Preview" class="w-full h-64 object-contain rounded-md" />
								<Button
									type="button"
									variant="destructive"
									size="icon"
									class="absolute top-2 right-2"
									onclick={removeImage}
								>
									<X class="h-4 w-4" />
								</Button>
							</div>
						{:else}
							<div
								class="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer transition-colors {isDragging
									? 'border-primary bg-primary/10'
									: 'border-muted-foreground/25 hover:bg-muted/50'}"
								onclick={() => triggerFileInput('found')}
								ondragover={handleDragOver}
								ondragleave={handleDragLeave}
								ondrop={handleDrop}
							>
								<Upload class="h-8 w-8 text-muted-foreground mb-2" />
								<span class="text-sm text-muted-foreground">Click to upload or drag and drop (Required)</span>
								<input
									bind:this={fileInputFound}
									id="image-input-found"
									type="file"
									accept="image/*"
									class="hidden"
									onchange={handleImageSelect}
									disabled={loading}
									required
								/>
							</div>
						{/if}
						<p class="text-xs text-muted-foreground">JPEG, PNG, or WebP (max 5MB)</p>
					</div>

					<Button type="button" class="w-full" onclick={handleSubmit} disabled={loading}>
						{loading ? 'Reporting...' : 'Report Found Item'}
					</Button>
				</TabsContent>
			</Tabs>
		</CardContent>
	</Card>
</div>

