<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { login, getCurrentUser } from '$lib/api/auth';
	import { authStore } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { AlertCircle } from "@lucide/svelte";
	import { toast } from 'svelte-sonner';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let error = $state<string | null>(null);

	async function handleLogin() {
		if (!email || !password) {
			error = 'Please fill in all fields';
			return;
		}

		loading = true;
		error = null;

		try {
			await login({ email, password });
			await authStore.init();
			await authStore.setUser(await getCurrentUser());
			toast.success('Welcome back!', {
				description: 'You have been successfully logged in.'
			});
			await goto(authStore.isAdmin ? '/dashboard/admin' : '/dashboard');
		} catch (err) {
			const errorMessage = err instanceof Error ? err.message : 'Login failed. Please try again.';
			error = errorMessage;
			toast.error('Login failed', {
				description: errorMessage
			});
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-muted/20 to-background p-3 sm:p-4 md:p-6">
	<Card class="w-full max-w-md shadow-lg border-2">
		<CardHeader class="space-y-2 pb-4 sm:pb-6">
			<CardTitle class="text-2xl sm:text-3xl font-bold text-center tracking-tight">Welcome Back</CardTitle>
			<CardDescription class="text-center text-sm sm:text-base">Sign in to your account</CardDescription>
		</CardHeader>
		<CardContent class="px-4 sm:px-6">
			<form
				onsubmit={(e) => {
					e.preventDefault();
					handleLogin();
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
					<Label for="email">Email</Label>
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
					<Label for="password">Password</Label>
					<Input
						id="password"
						type="password"
						placeholder="••••••••"
						bind:value={password}
						disabled={loading}
						required
						autocomplete="current-password"
					/>
				</div>

				<Button type="submit" class="w-full touch-manipulation" disabled={loading}>
					{loading ? 'Signing in...' : 'Sign In'}
				</Button>

				<div class="text-center text-sm text-muted-foreground">
					Don't have an account?{' '}
					<a href="/register" class="text-primary hover:underline font-medium">Sign up</a>
				</div>
			</form>
		</CardContent>
	</Card>
</div>

