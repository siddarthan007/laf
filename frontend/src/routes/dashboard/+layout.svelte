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
	import { Home, Search, FileQuestion, CheckCircle, Settings, LogOut, Shield, Menu, X, Package, Sparkles } from "@lucide/svelte";
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { setUserContext } from '$lib/contexts/user.svelte';
	import { fly, fade } from 'svelte/transition';
	import { afterNavigate } from '$app/navigation';

	let { children } = $props();
	let mobileMenuOpen = $state(false);

	// Initialize user context
	const userContext = setUserContext();

	onMount(async () => {
		await userContext.init();
	});

	afterNavigate(() => {
		mobileMenuOpen = false;
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

<div class="min-h-screen flex flex-col relative overflow-hidden">
	<!-- Floating Navbar -->
	<div class="fixed top-4 left-0 right-0 z-50 px-4 flex justify-center">
		<nav class="bg-white/100 dark:bg-gray-950/100 border border-white/20 dark:border-gray-800/50 rounded-2xl w-full max-w-7xl px-4 py-3 flex items-center justify-between transition-all duration-300 shadow-xl">
			<div class="flex items-center gap-2 sm:gap-4 md:gap-8">
				<!-- Mobile Menu Button -->
				<Button
					variant="ghost"
					size="icon"
					class="md:hidden touch-manipulation hover:bg-primary/10 hover:text-primary"
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
				<a href="/dashboard" class="flex items-center gap-2 group">
					<div class="bg-primary/10 p-1.5 rounded-lg group-hover:bg-primary/20 transition-colors">
						<Sparkles class="h-5 w-5 text-primary" />
					</div>
					<span class="text-lg sm:text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600 tracking-tight">Findora</span>
				</a>

				<!-- Desktop Navigation -->
				<div class="hidden md:flex items-center gap-1">
					{#if authStore.isAdmin}
						<a
							href="/dashboard/admin"
							class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 {currentPath.startsWith('/dashboard/admin')
								? 'bg-primary/10 text-primary shadow-sm'
								: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
						>
							<Shield class="inline h-4 w-4 mr-2" />
							Admin
						</a>
					{:else}
						<a
							href="/dashboard"
							class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 {currentPath === '/dashboard'
								? 'bg-primary/10 text-primary shadow-sm'
								: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
						>
							<Home class="inline h-4 w-4 mr-2" />
							Dashboard
						</a>
						<a
							href="/dashboard/found"
							class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 {currentPath === '/dashboard/found'
								? 'bg-primary/10 text-primary shadow-sm'
								: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
						>
							<Search class="inline h-4 w-4 mr-2" />
							Browse Found
						</a>
						<a
							href="/dashboard/report"
							class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 {currentPath === '/dashboard/report'
								? 'bg-primary/10 text-primary shadow-sm'
								: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
						>
							<FileQuestion class="inline h-4 w-4 mr-2" />
							Report Item
						</a>
						<a
							href="/dashboard/matches"
							class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 {currentPath === '/dashboard/matches'
								? 'bg-primary/10 text-primary shadow-sm'
								: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
						>
							<CheckCircle class="inline h-4 w-4 mr-2" />
							Matches
						</a>
						<a
							href="/dashboard/my-items"
							class="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 {currentPath === '/dashboard/my-items'
								? 'bg-primary/10 text-primary shadow-sm'
								: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
						>
							<Package class="inline h-4 w-4 mr-2" />
							My Items
						</a>
					{/if}
				</div>
			</div>

			<DropdownMenu>
				<DropdownMenuTrigger
					class="inline-flex items-center gap-2 rounded-full pl-1 pr-3 py-1 text-sm font-medium transition-all hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 touch-manipulation border border-transparent hover:border-border/50"
				>
					<Avatar class="size-8 ring-2 ring-background">
						<AvatarFallback class="bg-primary/10 text-primary text-xs font-bold">{getInitials(authStore.user?.name || 'U')}</AvatarFallback>
					</Avatar>
					<span class="hidden lg:inline text-sm font-medium opacity-90">{authStore.user?.name}</span>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="end" class="w-56 bg-popover border-border">
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
						class="text-destructive focus:text-destructive"
					>
						<LogOut class="mr-2 h-4 w-4" />
						Log out
					</DropdownMenuItem>
				</DropdownMenuContent>
			</DropdownMenu>
		</nav>
	</div>

	<!-- Mobile Menu Overlay -->
	{#if mobileMenuOpen}
		<div 
			class="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden pt-24 px-4"
			transition:fade={{ duration: 200 }}
			onclick={() => (mobileMenuOpen = false)}
		>
			<div 
				class="bg-popover rounded-2xl p-2 space-y-1 shadow-2xl border-border"
				transition:fly={{ y: -20, duration: 300 }}
				onclick={(e) => e.stopPropagation()}
			>
				{#if authStore.isAdmin}
					<a
						href="/dashboard/admin"
						class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors {currentPath.startsWith('/dashboard/admin')
							? 'bg-primary/10 text-primary'
							: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
					>
						<Shield class="h-5 w-5" />
						Admin
					</a>
				{:else}
					<a
						href="/dashboard"
						class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors {currentPath === '/dashboard'
							? 'bg-primary/10 text-primary'
							: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
					>
						<Home class="h-5 w-5" />
						Dashboard
					</a>
					<a
						href="/dashboard/found"
						class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors {currentPath === '/dashboard/found'
							? 'bg-primary/10 text-primary'
							: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
					>
						<Search class="h-5 w-5" />
						Browse Found
					</a>
					<a
						href="/dashboard/report"
						class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors {currentPath === '/dashboard/report'
							? 'bg-primary/10 text-primary'
							: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
					>
						<FileQuestion class="h-5 w-5" />
						Report Item
					</a>
					<a
						href="/dashboard/matches"
						class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors {currentPath === '/dashboard/matches'
							? 'bg-primary/10 text-primary'
							: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
					>
						<CheckCircle class="h-5 w-5" />
						My Matches
					</a>
					<a
						href="/dashboard/my-items"
						class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors {currentPath === '/dashboard/my-items'
							? 'bg-primary/10 text-primary'
							: 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'}"
					>
						<Package class="h-5 w-5" />
						My Items
					</a>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Main Content -->
	<main class="flex-1 container mx-auto px-4 pt-28 pb-12 max-w-7xl relative z-0">
		{@render children()}
	</main>
</div>
