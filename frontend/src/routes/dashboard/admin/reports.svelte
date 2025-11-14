<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { Button } from '$lib/components/ui/button';
	import { Tabs, TabsContent, TabsList, TabsTrigger } from '$lib/components/ui/tabs';
	import { reportOnBehalf, reportOfficeItem } from '$lib/api/admin';
	import { AlertCircle, Upload, X, CheckCircle2 } from "@lucide/svelte";
	import { getUserContext } from '$lib/contexts/user.svelte';

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

	let activeTab = $state<'behalf' | 'office'>('behalf');
	let userIdentifier = $state('');
	let itemStatus = $state<'LOST' | 'FOUND'>('FOUND');
	let description = $state('');
	let location = $state('');
	let imageFile = $state<File | null>(null);
	let imagePreview = $state<string | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let success = $state(false);
	let isDragging = $state(false);
	let fileInputBehalf: HTMLInputElement | null = $state(null);
	let fileInputOffice: HTMLInputElement | null = $state(null);
	let reportedUser = $state<{ name: string; email: string; contact_number: string } | null>(null);
	
	const userContext = getUserContext();
	
	let imageRequired = $derived(itemStatus === 'FOUND');

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

	function triggerFileInput(inputId: 'behalf' | 'office') {
		const input = inputId === 'behalf' ? fileInputBehalf : fileInputOffice;
		input?.click();
	}

	function removeImage() {
		imageFile = null;
		imagePreview = null;
	}

	async function handleReportOnBehalf() {
		if (!userIdentifier || !description || !location) {
			error = 'Please fill in all required fields';
			return;
		}
		
		if (itemStatus === 'FOUND' && !imageFile) {
			error = 'Found items require an image';
			return;
		}

		loading = true;
		error = null;
		success = false;
		reportedUser = null;

		try {
			const item = await reportOnBehalf({
				user_identifier: userIdentifier,
				item_status: itemStatus,
				description,
				location,
				image: imageFile || undefined
			});
			success = true;
			reportedUser = item.reported_by;
			userIdentifier = '';
			itemStatus = 'FOUND';
			description = '';
			location = '';
			imageFile = null;
			imagePreview = null;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to report item. Please try again.';
		} finally {
			loading = false;
		}
	}

	async function handleReportOffice() {
		if (!description || !location || !imageFile) {
			error = 'Please fill in all required fields including image';
			return;
		}

		loading = true;
		error = null;
		success = false;

		try {
			await reportOfficeItem({
				item_status: 'FOUND',
				description,
				location,
				image: imageFile
			});
			success = true;
			description = '';
			location = '';
			imageFile = null;
			imagePreview = null;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to report item. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<Card>
	<CardHeader>
		<CardTitle>Report Items</CardTitle>
		<CardDescription>Report items on behalf of users or the admin office</CardDescription>
	</CardHeader>
	<CardContent>
		<Tabs bind:value={activeTab}>
			<TabsList class="grid w-full grid-cols-2 gap-1 sm:gap-2">
				<TabsTrigger value="behalf" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation whitespace-nowrap">Report on Behalf</TabsTrigger>
				<TabsTrigger value="office" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation whitespace-nowrap">Office Found Item</TabsTrigger>
			</TabsList>

			<TabsContent value="behalf" class="space-y-4 mt-4">
				{#if error}
					<div class="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
						<AlertCircle class="h-4 w-4" />
						<span>{error}</span>
					</div>
				{/if}

				{#if success}
					<div class="space-y-2">
						<div class="flex items-center gap-2 p-3 text-sm text-green-600 bg-green-50 rounded-md">
							<CheckCircle2 class="h-4 w-4" />
							<span>Item reported successfully!</span>
						</div>
						{#if reportedUser}
							<div class="p-3 text-sm bg-muted rounded-md">
								<div class="font-medium mb-1">Reported by:</div>
								<div class="text-muted-foreground space-y-0.5">
									<div>{reportedUser.name}</div>
									<div>{reportedUser.email}</div>
									<div>{reportedUser.contact_number}</div>
								</div>
							</div>
						{/if}
					</div>
				{/if}

				<div class="space-y-2">
					<Label for="user-identifier">User Email or Roll Number *</Label>
					<Input
						id="user-identifier"
						type="text"
						placeholder="user@university.edu or 2024CS001"
						bind:value={userIdentifier}
						disabled={loading}
						required
					/>
				</div>

				<div class="space-y-2">
					<Label for="item-status-behalf">Item Status *</Label>
					<Select
						type="single"
						bind:value={itemStatus}
						disabled={loading}
					>
						<SelectTrigger>
							{itemStatus === 'LOST' ? 'Lost Item' : 'Found Item'}
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="LOST">Lost Item</SelectItem>
							<SelectItem value="FOUND">Found Item</SelectItem>
						</SelectContent>
					</Select>
				</div>

				<div class="space-y-2">
					<Label for="description-behalf">Description *</Label>
					<Textarea
						id="description-behalf"
						placeholder="Describe the item"
						bind:value={description}
						disabled={loading}
						required
						rows={4}
					/>
				</div>

				<div class="space-y-2">
					<Label for="location-behalf">Location *</Label>
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
					<Label for="image-behalf">Image {imageRequired ? '*' : '(Optional)'}</Label>
					{#if imagePreview}
						<div class="relative w-full h-48 bg-muted rounded-md overflow-hidden flex items-center justify-center">
							<img src={imagePreview} alt="Preview" class="max-w-full max-h-full object-contain rounded-md" />
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
							onclick={() => triggerFileInput('behalf')}
							ondragover={handleDragOver}
							ondragleave={handleDragLeave}
							ondrop={handleDrop}
						>
							<Upload class="h-8 w-8 text-muted-foreground mb-2" />
							<span class="text-sm text-muted-foreground">Click to upload or drag and drop</span>
							<input
								bind:this={fileInputBehalf}
								id="image-input-behalf"
								type="file"
								accept="image/*"
								class="hidden"
								onchange={handleImageSelect}
								disabled={loading}
								required={imageRequired}
							/>
						</div>
					{/if}
				</div>

				<Button type="button" class="w-full" onclick={handleReportOnBehalf} disabled={loading}>
					{loading ? 'Reporting...' : 'Report Item'}
				</Button>
			</TabsContent>

			<TabsContent value="office" class="space-y-4 mt-4">
				{#if error}
					<div class="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
						<AlertCircle class="h-4 w-4" />
						<span>{error}</span>
					</div>
				{/if}

				{#if success}
					<div class="space-y-2">
						<div class="flex items-center gap-2 p-3 text-sm text-green-600 bg-green-50 rounded-md">
							<CheckCircle2 class="h-4 w-4" />
							<span>Item reported successfully!</span>
						</div>
					</div>
				{/if}

				<div class="space-y-2">
					<Label for="description-office">Description *</Label>
					<Textarea
						id="description-office"
						placeholder="Describe the found item"
						bind:value={description}
						disabled={loading}
						required
						rows={4}
					/>
				</div>

				<div class="space-y-2">
					<Label for="location-office">Location *</Label>
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
					<Label for="image-office">Image *</Label>
					{#if imagePreview}
						<div class="relative w-full h-48 bg-muted rounded-md overflow-hidden flex items-center justify-center">
							<img src={imagePreview} alt="Preview" class="max-w-full max-h-full object-contain rounded-md" />
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
							onclick={() => triggerFileInput('office')}
							ondragover={handleDragOver}
							ondragleave={handleDragLeave}
							ondrop={handleDrop}
						>
							<Upload class="h-8 w-8 text-muted-foreground mb-2" />
							<span class="text-sm text-muted-foreground">Click to upload or drag and drop (Required)</span>
							<input
								bind:this={fileInputOffice}
								id="image-input-office"
								type="file"
								accept="image/*"
								class="hidden"
								onchange={handleImageSelect}
								disabled={loading}
								required
							/>
						</div>
					{/if}
				</div>

				<Button type="button" class="w-full" onclick={handleReportOffice} disabled={loading}>
					{loading ? 'Reporting...' : 'Report Office Item'}
				</Button>
			</TabsContent>
		</Tabs>
	</CardContent>
</Card>

