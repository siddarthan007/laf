<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { Separator } from '$lib/components/ui/separator';
	import { AlertCircle, CheckCircle2 } from '@lucide/svelte';
	import { onMount } from 'svelte';
	import { getUserContext } from '$lib/contexts/user.svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { toast } from 'svelte-sonner';

	const HOSTELS = [
		'Hostel A',
		'Hostel B',
		'Hostel C',
		'Hostel D',
		'Hostel E',
		'Hostel F',
		'Hostel G',
		'Hostel H',
		'Hostel I',
		'Hostel J',
		'Hostel K',
		'Hostel L',
		'Hostel M',
		'Hostel N',
		'Hostel O'
	];

	const userContext = getUserContext();

	let name = $state('');
	let email = $state('');
	let hostel = $state('');
	let contactNumber = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let loading = $state(false);
	let error = $state<string | null>(null);
	let success = $state(false);

	onMount(async () => {
		await userContext.init();
		const user = userContext.user;
		if (user) {
			name = user.name;
			email = user.email;
			hostel = user.hostel || '';
			contactNumber = user.contact_number;
		}
	});

	async function handleSubmit() {
		error = null;
		success = false;

		// Validate password if provided
		if (password) {
			if (password.length < 8) {
				error = 'Password must be at least 8 characters long';
				return;
			}
			if (password !== confirmPassword) {
				error = 'Passwords do not match';
				return;
			}
		}

		loading = true;

		try {
			const updateData: Record<string, string> = {};
			if (name !== userContext.user?.name) updateData.name = name;
			if (email !== userContext.user?.email) updateData.email = email;
			if (hostel !== (userContext.user?.hostel || '')) updateData.hostel = hostel;
			if (contactNumber !== userContext.user?.contact_number) updateData.contact_number = contactNumber;
			if (password) updateData.password = password;

			if (Object.keys(updateData).length === 0) {
				error = 'No changes to save';
				loading = false;
				return;
			}

			const updatedUser = await userContext.update(updateData);
			
			// Update auth store
			await authStore.setUser(updatedUser);

			success = true;
			password = '';
			confirmPassword = '';
			
			toast.success('Profile updated', {
				description: 'Your profile has been updated successfully.'
			});

			setTimeout(() => {
				success = false;
			}, 3000);
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Failed to update profile. Please try again.';
			error = errorMessage;
			toast.error('Failed to update profile', {
				description: errorMessage
			});
		} finally {
			loading = false;
		}
	}
</script>

<div class="max-w-2xl mx-auto space-y-6 px-4">
	<div>
		<h1 class="text-3xl font-bold">Settings</h1>
		<p class="text-muted-foreground mt-2">Manage your account information</p>
	</div>

	<Card>
		<CardHeader>
			<CardTitle>Profile Information</CardTitle>
			<CardDescription>Update your personal information and preferences</CardDescription>
		</CardHeader>
		<CardContent class="space-y-6">
			{#if error}
				<div class="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
					<AlertCircle class="h-4 w-4" />
					<span>{error}</span>
				</div>
			{/if}

			{#if success}
				<div class="flex items-center gap-2 p-3 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/30 rounded-md">
					<CheckCircle2 class="h-4 w-4" />
					<span>Profile updated successfully!</span>
				</div>
			{/if}

			<div class="space-y-4">
				<div class="space-y-2">
					<Label for="name">Full Name *</Label>
					<Input
						id="name"
						type="text"
						placeholder="Enter your full name"
						bind:value={name}
						disabled={loading}
						required
					/>
				</div>

				<div class="space-y-2">
					<Label for="email">Email *</Label>
					<Input
						id="email"
						type="email"
						placeholder="Enter your email"
						bind:value={email}
						disabled={loading}
						required
					/>
				</div>

				<div class="space-y-2">
					<Label for="hostel">Hostel</Label>
					<Select type="single" bind:value={hostel}>
						<SelectTrigger>
							{hostel || 'Select hostel'}
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="">None</SelectItem>
							{#each HOSTELS as h}
								<SelectItem value={h}>{h}</SelectItem>
							{/each}
						</SelectContent>
					</Select>
				</div>

				<div class="space-y-2">
					<Label for="contact">Contact Number *</Label>
					<Input
						id="contact"
						type="tel"
						placeholder="Enter your contact number"
						bind:value={contactNumber}
						disabled={loading}
						required
					/>
				</div>
			</div>

			<Separator />

			<div class="space-y-4">
				<h3 class="text-lg font-semibold">Change Password</h3>
				<p class="text-sm text-muted-foreground">Leave blank if you don't want to change your password</p>

				<div class="space-y-2">
					<Label for="password">New Password</Label>
					<Input
						id="password"
						type="password"
						placeholder="Enter new password (min 8 characters)"
						bind:value={password}
						disabled={loading}
					/>
				</div>

				<div class="space-y-2">
					<Label for="confirm-password">Confirm New Password</Label>
					<Input
						id="confirm-password"
						type="password"
						placeholder="Confirm new password"
						bind:value={confirmPassword}
						disabled={loading}
					/>
				</div>
			</div>

			<Button type="button" class="w-full" onclick={handleSubmit} disabled={loading}>
				{loading ? 'Saving...' : 'Save Changes'}
			</Button>
		</CardContent>
	</Card>
</div>

