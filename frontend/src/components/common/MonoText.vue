<script setup lang="ts">
import { cn } from '@/lib/utils'
defineProps<{ class?: string }>()
</script>

<template>
  <span :class="cn('font-mono text-[0.875em] tracking-tight', $props.class)">
    <slot />
  </span>
</template>
