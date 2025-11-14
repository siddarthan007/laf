<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Select, SelectContent, SelectItem, SelectTrigger } from '$lib/components/ui/select';
	import { register, login } from '$lib/api/auth';
	import { authStore } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { AlertCircle } from "@lucide/svelte";
	import { getCurrentUser } from '$lib/api/auth';
	import { toast } from 'svelte-sonner';

	const HOSTELS = ['Hostel A', 'Hostel B', 'Hostel C', 'Hostel D', 'Hostel E', 'Hostel F', 'Hostel G', 'Hostel H', 'Hostel I', 'Hostel J', 'Hostel K', 'Hostel L', 'Hostel M', 'Hostel N', 'Hostel O'];

	let name = $state('');
	let email = $state('');
	let password = $state('');
	let rollNumber = $state('');
	let hostel = $state('');
	let contactNumber = $state('');
	let loading = $state(false);
	let error = $state<string | null>(null);

	async function handleRegister() {
		if (!name || !email || !password || !rollNumber || !contactNumber || !hostel) {
			error = 'Please fill in all required fields';
			return;
		}

		loading = true;
		error = null;

		try {
			await register({
				name,
				email,
				password,
				roll_number: rollNumber,
				hostel,
				contact_number: contactNumber
			});

			toast.success('Account created!', {
				description: 'Your account has been created successfully.'
			});

			// Auto-login after registration
			await login({ email, password });
			await authStore.init();
			await authStore.setUser(await getCurrentUser());
			await goto(authStore.isAdmin ? '/dashboard/admin' : '/dashboard');
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Registration failed. Please try again.';
			error = errorMessage;
			toast.error('Registration failed', {
				description: errorMessage
			});
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-muted/20 to-background p-4 sm:p-6">
	<Card class="w-full max-w-md shadow-lg border-2">
		<CardHeader class="space-y-2 pb-6">
			<CardTitle class="text-3xl font-bold text-center tracking-tight">Create Account</CardTitle>
			<CardDescription class="text-center text-base">Sign up for Lost & Found</CardDescription>
		</CardHeader>
		<CardContent>
			<form
				onsubmit={(e) => {
					e.preventDefault();
					handleRegister();
				}}
				class="space-y-4"
			>
				{#if error}
					<div class="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
						<AlertCircle class="h-4 w-4" />
						<span>{error}</span>
					</div>
				{/if}

				<div class="space-y-2">
					<Label for="name">Full Name *</Label>
					<Input
						id="name"
						type="text"
						placeholder="John Doe"
						bind:value={name}
						disabled={loading}
						required
						autocomplete="name"
					/>
				</div>

				<div class="space-y-2">
					<Label for="email">Email *</Label>
					<Input
						id="email"
						type="email"
						placeholder="john.doe@university.edu"
						bind:value={email}
						disabled={loading}
						required
						autocomplete="email"
					/>
				</div>

				<div class="space-y-2">
					<Label for="rollNumber">Roll Number *</Label>
					<Input
						id="rollNumber"
						type="text"
						placeholder="2024CS001"
						bind:value={rollNumber}
						disabled={loading}
						required
					/>
				</div>

				<div class="space-y-2">
					<Label for="hostel">Hostel *</Label>
					<Select
						type="single"
						bind:value={hostel}
						disabled={loading}
						required
					>
						<SelectTrigger id="hostel">
							{hostel || 'Select hostel'}
						</SelectTrigger>
						<SelectContent>
							{#each HOSTELS as h}
								<SelectItem value={h}>{h}</SelectItem>
							{/each}
						</SelectContent>
					</Select>
				</div>

				<div class="space-y-2">
					<Label for="contactNumber">Contact Number *</Label>
					<Input
						id="contactNumber"
						type="tel"
						placeholder="+1234567890"
						bind:value={contactNumber}
						disabled={loading}
						required
						autocomplete="tel"
					/>
				</div>

				<div class="space-y-2">
					<Label for="password">Password *</Label>
					<Input
						id="password"
						type="password"
						placeholder="••••••••"
						bind:value={password}
						disabled={loading}
						required
						minlength={8}
						autocomplete="new-password"
					/>
				</div>

				<Button type="submit" class="w-full" disabled={loading}>
					{loading ? 'Creating account...' : 'Sign Up'}
				</Button>

				<div class="text-center text-sm text-muted-foreground">
					Already have an account?{' '}
					<a href="/login" class="text-primary hover:underline font-medium">Sign in</a>
				</div>
			</form>
		</CardContent>
	</Card>
</div>

