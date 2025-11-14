<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Tabs, TabsContent, TabsList, TabsTrigger } from '$lib/components/ui/tabs';
	import { getAnalytics } from '$lib/api/admin';
	import { onMount } from 'svelte';
	import { Users, Package, CheckCircle, TrendingUp, Shield } from "@lucide/svelte";
	import type { Analytics } from '$lib/api/admin';
import AdminUsers from './users.svelte';
import AdminItems from './items.svelte';
import AdminMatches from './matches.svelte';
import AdminReports from './reports.svelte';
import AdminMyItems from './my-items.svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';

	let analytics = $state<Analytics | null>(null);
	let loading = $state(true);
	let activeTab = $state('my-items');

	onMount(async () => {
		// Ensure user is admin
		if (!authStore.isAdmin) {
			await goto('/dashboard');
			return;
		}

		try {
			analytics = await getAnalytics();
		} catch (err) {
			console.error('Failed to load analytics:', err);
		} finally {
			loading = false;
		}
	});
</script>

{#if !authStore.isAdmin}
	<div class="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
		<Shield class="h-16 w-16 text-muted-foreground" />
		<h2 class="text-2xl font-bold">Access Denied</h2>
		<p class="text-muted-foreground">You need admin privileges to access this page.</p>
	</div>
{:else}
	<div class="space-y-4 sm:space-y-6">
		<div>
			<h1 class="text-2xl sm:text-3xl font-bold flex items-center gap-2">
				<Shield class="h-6 w-6 sm:h-8 sm:w-8" />
				Admin Dashboard
			</h1>
			<p class="text-muted-foreground mt-1 sm:mt-2 text-sm sm:text-base">Manage users, items, and matches</p>
		</div>

	{#if loading}
		<div class="text-center py-12 text-muted-foreground">Loading analytics...</div>
	{:else if analytics}
		<div class="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 auto-rows-fr">
			<Card>
				<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
					<CardTitle class="text-sm font-medium">Total Users</CardTitle>
					<Users class="h-4 w-4 text-muted-foreground" />
				</CardHeader>
				<CardContent>
					<div class="text-2xl font-bold">{analytics.totals.users}</div>
					<p class="text-xs text-muted-foreground">Registered users</p>
				</CardContent>
			</Card>

			<Card>
				<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
					<CardTitle class="text-sm font-medium">Active Items</CardTitle>
					<Package class="h-4 w-4 text-muted-foreground" />
				</CardHeader>
				<CardContent>
					<div class="text-2xl font-bold">
						{analytics.totals.lost_active + analytics.totals.found_active}
					</div>
					<p class="text-xs text-muted-foreground">
						{analytics.totals.lost_active} lost, {analytics.totals.found_active} found
					</p>
				</CardContent>
			</Card>

			<Card>
				<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
					<CardTitle class="text-sm font-medium">Resolved Items</CardTitle>
					<CheckCircle class="h-4 w-4 text-muted-foreground" />
				</CardHeader>
				<CardContent>
					<div class="text-2xl font-bold">{analytics.totals.resolved}</div>
					<p class="text-xs text-muted-foreground">Successfully matched</p>
				</CardContent>
			</Card>

			<Card>
				<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
					<CardTitle class="text-sm font-medium">Pending Matches</CardTitle>
					<TrendingUp class="h-4 w-4 text-muted-foreground" />
				</CardHeader>
				<CardContent>
					<div class="text-2xl font-bold">{analytics.totals.matches_pending}</div>
					<p class="text-xs text-muted-foreground">Awaiting approval</p>
				</CardContent>
			</Card>
		</div>

		<Tabs bind:value={activeTab} class="mt-4 sm:mt-6">
			<TabsList class="grid w-full grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1 sm:gap-2 overflow-x-auto">
				<TabsTrigger value="my-items" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation whitespace-nowrap">My Admin Items</TabsTrigger>
				<TabsTrigger value="reports" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation whitespace-nowrap">Report Items</TabsTrigger>
				<TabsTrigger value="users" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation whitespace-nowrap">Users</TabsTrigger>
				<TabsTrigger value="items" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation whitespace-nowrap">Items</TabsTrigger>
				<TabsTrigger value="matches" class="text-xs sm:text-sm px-2 sm:px-3 py-2 touch-manipulation whitespace-nowrap">Matches</TabsTrigger>
			</TabsList>

			<TabsContent value="my-items" class="mt-4">
				<AdminMyItems />
			</TabsContent>

			<TabsContent value="reports" class="mt-4">
				<AdminReports />
			</TabsContent>

			<TabsContent value="users" class="mt-4">
				<AdminUsers />
			</TabsContent>

			<TabsContent value="items" class="mt-4">
				<AdminItems />
			</TabsContent>

			<TabsContent value="matches" class="mt-4">
				<AdminMatches />
			</TabsContent>
		</Tabs>
	{/if}
	</div>
{/if}

