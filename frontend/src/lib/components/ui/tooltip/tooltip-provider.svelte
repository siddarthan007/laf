<script lang="ts">
	import { Tooltip as TooltipPrimitive } from "bits-ui";
	import { onMount } from "svelte";
	
	let mounted = $state(false);
	
	onMount(() => {
		mounted = true;
	});
	
	let { delayDuration = 0, skipDelayDuration = 0, disableHoverableContent = false, children } = $props();
</script>

{#if mounted}
	<TooltipPrimitive.Provider
		{delayDuration}
		{skipDelayDuration}
		{disableHoverableContent}
	>
		{@render children()}
	</TooltipPrimitive.Provider>
{:else}
	{@render children()}
{/if}

