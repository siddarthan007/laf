<script lang="ts">
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import { getUsers } from '$lib/api/admin';
	import { onMount } from 'svelte';
	import type { User } from '$lib/api/auth';
	import { Users, Search, X } from "@lucide/svelte";

	let users = $state<User[]>([]);
	let filteredUsers = $derived.by(() => {
		if (!searchQuery.trim()) return users;
		const query = searchQuery.toLowerCase().trim();
		return users.filter(user => 
			user.name.toLowerCase().includes(query) ||
			user.email.toLowerCase().includes(query) ||
			user.roll_number.toLowerCase().includes(query) ||
			(user.hostel && user.hostel.toLowerCase().includes(query)) ||
			user.contact_number.includes(query)
		);
	});
	let loading = $state(false);
	let offset = $state(0);
	let searchQuery = $state('');
	const limit = 50;

	onMount(async () => {
		await loadUsers();
	});

	async function loadUsers() {
		loading = true;
		try {
			users = await getUsers({ limit, offset });
		} catch (err) {
			console.error('Failed to load users:', err);
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

	function clearSearch() {
		searchQuery = '';
	}
</script>

<Card>
	<CardHeader>
		<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
			<CardTitle class="flex items-center gap-2">
				<Users class="h-5 w-5" />
				Users ({filteredUsers.length})
			</CardTitle>
			<div class="relative w-full sm:w-auto sm:min-w-[300px]">
				<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
				<Input
					type="text"
					placeholder="Search by name, email, roll number..."
					bind:value={searchQuery}
					class="pl-9 pr-9 text-sm"
				/>
				{#if searchQuery}
					<button
						onclick={clearSearch}
						class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground touch-manipulation"
						aria-label="Clear search"
					>
						<X class="h-4 w-4" />
					</button>
				{/if}
			</div>
		</div>
	</CardHeader>
	<CardContent>
		{#if loading}
			<div class="text-center py-8 text-muted-foreground">Loading users...</div>
		{:else if filteredUsers.length === 0}
			<div class="text-center py-8 text-muted-foreground">
				{searchQuery ? 'No users found matching your search' : 'No users found'}
			</div>
		{:else}
			<!-- Mobile Card View -->
			<div class="block md:hidden space-y-3">
				{#each filteredUsers as user}
					<div class="border rounded-lg p-4 space-y-2 bg-card">
						<div class="flex items-start justify-between">
							<div class="flex-1 min-w-0">
								<p class="font-semibold text-sm truncate">{user.name}</p>
								<p class="text-xs text-muted-foreground break-all mt-1">{user.email}</p>
							</div>
							<Badge variant={user.role === 'ADMIN' ? 'default' : 'secondary'} class="text-xs flex-shrink-0 ml-2">
								{user.role}
							</Badge>
						</div>
						<div class="grid grid-cols-2 gap-2 text-xs">
							<div>
								<p class="text-muted-foreground">Roll Number</p>
								<p class="font-mono font-medium">{user.roll_number}</p>
							</div>
							<div>
								<p class="text-muted-foreground">Hostel</p>
								<p class="font-medium">{user.hostel || '-'}</p>
							</div>
							<div>
								<p class="text-muted-foreground">Contact</p>
								<p class="font-medium">{user.contact_number}</p>
							</div>
							<div>
								<p class="text-muted-foreground">Joined</p>
								<p class="font-medium">{formatDate(user.created_at)}</p>
							</div>
						</div>
					</div>
				{/each}
			</div>
			<!-- Desktop Table View -->
			<div class="hidden md:block overflow-x-auto -mx-4 px-4">
				<table class="w-full min-w-[800px]">
					<thead>
						<tr class="border-b">
							<th class="text-left p-3 font-semibold text-sm">Name</th>
							<th class="text-left p-3 font-semibold text-sm">Email</th>
							<th class="text-left p-3 font-semibold text-sm">Roll Number</th>
							<th class="text-left p-3 font-semibold text-sm">Hostel</th>
							<th class="text-left p-3 font-semibold text-sm">Contact</th>
							<th class="text-left p-3 font-semibold text-sm">Role</th>
							<th class="text-left p-3 font-semibold text-sm">Joined</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredUsers as user}
							<tr class="border-b hover:bg-muted/50 transition-colors">
								<td class="p-3 text-sm font-medium">{user.name}</td>
								<td class="p-3 text-sm break-all">{user.email}</td>
								<td class="p-3 text-sm font-mono">{user.roll_number}</td>
								<td class="p-3 text-sm">{user.hostel || '-'}</td>
								<td class="p-3 text-sm">{user.contact_number}</td>
								<td class="p-3">
									<Badge variant={user.role === 'ADMIN' ? 'default' : 'secondary'} class="text-xs">
										{user.role}
									</Badge>
								</td>
								<td class="p-3 text-sm text-muted-foreground">{formatDate(user.created_at)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</CardContent>
</Card>

