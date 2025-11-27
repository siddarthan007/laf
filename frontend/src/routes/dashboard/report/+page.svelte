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
	import { fade, fly } from 'svelte/transition';

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

<div class="max-w-2xl mx-auto space-y-8 px-4 pb-12" in:fade={{ duration: 300 }}>
	<div class="space-y-2 text-center sm:text-left">
		<h1 class="text-3xl md:text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600 inline-block">Report Item</h1>
		<p class="text-muted-foreground text-lg">Help us connect lost items with their owners</p>
	</div>

	<div class="glass rounded-3xl p-1 shadow-xl border border-white/20" in:fly={{ y: 20, duration: 500, delay: 100 }}>
		<div class="bg-card/50 backdrop-blur-sm rounded-[1.4rem] p-6 sm:p-8">
			<Tabs bind:value={activeTab} class="w-full">
				<TabsList class="grid w-full grid-cols-2 mb-8 p-1 bg-muted/50 rounded-xl">
					<TabsTrigger value="lost" class="rounded-lg data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all duration-300">Lost Item</TabsTrigger>
					<TabsTrigger value="found" class="rounded-lg data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm transition-all duration-300">Found Item</TabsTrigger>
				</TabsList>

				<div class="space-y-6">
					{#if error}
						<div class="flex items-center gap-3 p-4 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl" transition:fly={{ y: -10, duration: 200 }}>
							<AlertCircle class="h-5 w-5 flex-shrink-0" />
							<span class="font-medium">{error}</span>
						</div>
					{/if}

					{#if success}
						<div class="space-y-3" transition:fly={{ y: -10, duration: 200 }}>
							<div class="flex items-center gap-3 p-4 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900/50 rounded-xl">
								<CheckCircle2 class="h-5 w-5 flex-shrink-0" />
								<span class="font-medium">Item reported successfully! Checking for matches...</span>
							</div>
							{#if matchesFound !== null && matchesFound > 0}
								<div class="flex items-center gap-3 p-4 text-sm text-primary bg-primary/10 border border-primary/20 rounded-xl" transition:fly={{ y: 10, duration: 300 }}>
									<CheckCircle2 class="h-5 w-5 flex-shrink-0" />
									<span class="font-medium">Found {matchesFound} potential match{matchesFound !== 1 ? 'es' : ''}! Check your matches page.</span>
								</div>
							{:else if matchesFound === 0}
								<div class="flex items-center gap-3 p-4 text-sm text-muted-foreground bg-muted/50 border border-border rounded-xl" transition:fly={{ y: 10, duration: 300 }}>
									<AlertCircle class="h-5 w-5 flex-shrink-0" />
									<span>No matches found yet. We'll notify you if any potential matches are found.</span>
								</div>
							{/if}
						</div>
					{/if}

					<div class="space-y-4">
						<div class="space-y-2">
							<Label for="description-{activeTab}" class="flex items-center gap-2 text-base font-medium">
								Description <span class="text-destructive">*</span>
								<Tooltip>
									<TooltipTrigger>
										<Info class="h-4 w-4 text-muted-foreground hover:text-primary transition-colors" />
									</TooltipTrigger>
									<TooltipContent>
										<p>Provide a detailed description to help others identify your item</p>
									</TooltipContent>
								</Tooltip>
							</Label>
							<Textarea
								id="description-{activeTab}"
								placeholder={activeTab === 'lost' ? "E.g., Black leather wallet with ID card..." : "E.g., Black wallet found near library..."}
								bind:value={description}
								disabled={loading}
								required
								rows={4}
								class="resize-none bg-background/50 border-border/50 focus:border-primary/50 focus:ring-primary/20 transition-all"
							/>
						</div>

						<div class="space-y-2">
							<Label for="location-{activeTab}" class="text-base font-medium">Location <span class="text-destructive">*</span></Label>
							<Select type="single" bind:value={location}>
								<SelectTrigger class="bg-background/50 border-border/50 focus:border-primary/50 focus:ring-primary/20 transition-all">
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
							<Label for="image-{activeTab}" class="flex items-center gap-2 text-base font-medium">
								Image {activeTab === 'found' ? '' : '(Optional)'} <span class={activeTab === 'found' ? 'text-destructive' : 'hidden'}>*</span>
								<Tooltip>
									<TooltipTrigger>
										<Info class="h-4 w-4 text-muted-foreground hover:text-primary transition-colors" />
									</TooltipTrigger>
									<TooltipContent>
										<p>Adding an image significantly increases the chance of finding a match</p>
									</TooltipContent>
								</Tooltip>
							</Label>
							
							{#if imagePreview}
								<div class="relative bg-muted/30 rounded-xl overflow-hidden border border-border/50 group" transition:fade>
									<img src={imagePreview} alt="Preview" class="w-full h-64 object-contain" />
									<div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
										<Button
											type="button"
											variant="destructive"
											size="sm"
											class="rounded-full"
											onclick={removeImage}
										>
											<X class="h-4 w-4 mr-2" /> Remove Image
										</Button>
									</div>
								</div>
							{:else}
								<div
									class="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300 {isDragging
										? 'border-primary bg-primary/5 scale-[1.02]'
										: 'border-muted-foreground/20 hover:border-primary/50 hover:bg-muted/30'}"
									onclick={() => triggerFileInput(activeTab)}
									ondragover={handleDragOver}
									ondragleave={handleDragLeave}
									ondrop={handleDrop}
									role="button"
									tabindex="0"
									onkeydown={(e) => e.key === 'Enter' && triggerFileInput(activeTab)}
								>
									<div class="p-4 rounded-full bg-primary/10 mb-3 group-hover:scale-110 transition-transform">
										<Upload class="h-6 w-6 text-primary" />
									</div>
									<span class="text-sm font-medium text-foreground">Click to upload or drag and drop</span>
									<span class="text-xs text-muted-foreground mt-1">JPEG, PNG, or WebP (max 5MB)</span>
									{#if activeTab === 'lost'}
									<input
										bind:this={fileInputLost}
										id="image-input-lost"
										type="file"
										accept="image/*"
										class="hidden"
										onchange={handleImageSelect}
										disabled={loading}
									/>
								{:else}
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
								{/if}
								</div>
							{/if}
						</div>
					</div>

					<Button 
						type="button" 
						class="w-full h-12 text-base font-medium rounded-xl shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all hover:-translate-y-0.5" 
						onclick={handleSubmit} 
						disabled={loading}
					>
						{#if loading}
							<span class="animate-pulse">Processing...</span>
						{:else}
							{activeTab === 'lost' ? 'Report Lost Item' : 'Report Found Item'}
						{/if}
					</Button>
				</div>
			</Tabs>
		</div>
	</div>
</div>
