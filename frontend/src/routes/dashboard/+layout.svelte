<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import { Avatar, AvatarFallback } from '$lib/components/ui/avatar';
	import {
		DropdownMenu,
		DropdownMenuContent,
		DropdownMenuItem,
		DropdownMenuLabel,
		DropdownMenuSeparator,
		DropdownMenuTrigger
	} from '$lib/components/ui/dropdown-menu';
	import { authStore } from '$lib/stores/auth.svelte';
	import { Home, Search, FileQuestion, CheckCircle, Settings, LogOut, Shield, Menu, X, Package } from "@lucide/svelte";
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { setUserContext } from '$lib/contexts/user.svelte';

	let { children } = $props();
	let mobileMenuOpen = $state(false);

	// Initialize user context
	const userContext = setUserContext();

	onMount(async () => {
		await userContext.init();
	});

	function getInitials(name: string) {
		return name
			.split(' ')
			.map((n) => n[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}

	let currentPath = $derived($page.url.pathname);
</script>

<div class="min-h-screen bg-background">
	<nav class="border-b bg-card/95 backdrop-blur-md sticky top-0 z-50 shadow-sm">
		<div class="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2 sm:gap-4 md:gap-8">
					<!-- Mobile Menu Button - Before Logo -->
					<Button
						variant="ghost"
						size="icon"
						class="md:hidden touch-manipulation"
						onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
						aria-label="Toggle navigation menu"
					>
						{#if mobileMenuOpen}
							<X class="h-5 w-5" />
						{:else}
							<Menu class="h-5 w-5" />
						{/if}
					</Button>
					<!-- Logo -->
					<a href="/dashboard" class="text-lg sm:text-xl md:text-2xl font-bold text-primary hover:text-primary/80 transition-colors tracking-tight">Findora</a>
					<!-- Desktop Navigation -->
					<div class="hidden md:flex items-center gap-1">
						{#if authStore.isAdmin}
							<a
								href="/dashboard/admin"
								class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentPath.startsWith('/dashboard/admin')
									? 'bg-primary text-primary-foreground shadow-sm'
									: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'}"
							>
								<Shield class="inline h-4 w-4 mr-2" />
								Admin
							</a>
						{:else}
							<a
								href="/dashboard"
								class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentPath === '/dashboard'
									? 'bg-primary text-primary-foreground shadow-sm'
									: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'}"
							>
								<Home class="inline h-4 w-4 mr-2" />
								Dashboard
							</a>
							<a
								href="/dashboard/found"
								class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentPath === '/dashboard/found'
									? 'bg-primary text-primary-foreground shadow-sm'
									: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'}"
							>
								<Search class="inline h-4 w-4 mr-2" />
								Browse Found
							</a>
							<a
								href="/dashboard/report"
								class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentPath === '/dashboard/report'
									? 'bg-primary text-primary-foreground shadow-sm'
									: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'}"
							>
								<FileQuestion class="inline h-4 w-4 mr-2" />
								Report Item
							</a>
							<a
								href="/dashboard/matches"
								class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentPath === '/dashboard/matches'
									? 'bg-primary text-primary-foreground shadow-sm'
									: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'}"
							>
								<CheckCircle class="inline h-4 w-4 mr-2" />
								My Matches
							</a>
							<a
								href="/dashboard/my-items"
								class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 {currentPath === '/dashboard/my-items'
									? 'bg-primary text-primary-foreground shadow-sm'
									: 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'}"
							>
								<Package class="inline h-4 w-4 mr-2" />
								My Items
							</a>
						{/if}
					</div>
				</div>

				<DropdownMenu>
					<DropdownMenuTrigger
						class="inline-flex items-center gap-1 sm:gap-2 rounded-md px-2 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 touch-manipulation"
					>
						<Avatar class="size-7 sm:size-8 md:size-9">
							<AvatarFallback class="text-xs sm:text-sm">{getInitials(authStore.user?.name || 'U')}</AvatarFallback>
						</Avatar>
						<span class="hidden lg:inline">{authStore.user?.name}</span>
					</DropdownMenuTrigger>
					<DropdownMenuContent align="end" class="w-56">
						<DropdownMenuLabel>My Account</DropdownMenuLabel>
						<DropdownMenuSeparator />
						<DropdownMenuItem>
							<a href="/dashboard/settings" class="flex items-center w-full">
								<Settings class="mr-2 h-4 w-4" />
								Settings
							</a>
						</DropdownMenuItem>
						<DropdownMenuSeparator />
						<DropdownMenuItem
							onclick={async () => {
								await authStore.logout();
							}}
						>
							<LogOut class="mr-2 h-4 w-4" />
							Log out
						</DropdownMenuItem>
					</DropdownMenuContent>
				</DropdownMenu>
			</div>
		</div>
		{#if mobileMenuOpen}
			<div class="md:hidden border-t bg-card">
				<div class="px-4 py-2 space-y-1">
					{#if authStore.isAdmin}
						<a
							href="/dashboard/admin"
							class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors {currentPath.startsWith('/dashboard/admin')
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:bg-muted hover:text-foreground'}"
							onclick={() => (mobileMenuOpen = false)}
						>
							<Shield class="h-4 w-4" />
							Admin
						</a>
					{:else}
						<a
							href="/dashboard"
							class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors {currentPath === '/dashboard'
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:bg-muted hover:text-foreground'}"
							onclick={() => (mobileMenuOpen = false)}
						>
							<Home class="h-4 w-4" />
							Dashboard
						</a>
						<a
							href="/dashboard/found"
							class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors {currentPath === '/dashboard/found'
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:bg-muted hover:text-foreground'}"
							onclick={() => (mobileMenuOpen = false)}
						>
							<Search class="h-4 w-4" />
							Browse Found
						</a>
						<a
							href="/dashboard/report"
							class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors {currentPath === '/dashboard/report'
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:bg-muted hover:text-foreground'}"
							onclick={() => (mobileMenuOpen = false)}
						>
							<FileQuestion class="h-4 w-4" />
							Report Item
						</a>
						<a
							href="/dashboard/matches"
							class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors {currentPath === '/dashboard/matches'
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:bg-muted hover:text-foreground'}"
							onclick={() => (mobileMenuOpen = false)}
						>
							<CheckCircle class="h-4 w-4" />
							My Matches
						</a>
						<a
							href="/dashboard/my-items"
							class="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors {currentPath === '/dashboard/my-items'
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:bg-muted hover:text-foreground'}"
							onclick={() => (mobileMenuOpen = false)}
						>
							<Package class="h-4 w-4" />
							My Items
						</a>
					{/if}
				</div>
			</div>
		{/if}
	</nav>

	<main class="container mx-auto px-3 sm:px-4 py-4 sm:py-6 md:py-8 max-w-7xl">
		{@render children()}
	</main>
</div>

