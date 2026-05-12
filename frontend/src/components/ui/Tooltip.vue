<script setup lang="ts">
import { cn } from '@/lib/utils'
const props = defineProps<{ text: string; class?: string; side?: 'top' | 'bottom' }>()
</script>

<template>
  <span :class="cn('relative inline-flex group', props.class)">
    <slot />
    <span
      :class="
        cn(
          'pointer-events-none absolute left-1/2 z-50 -translate-x-1/2 whitespace-nowrap rounded-md',
          'border border-border bg-popover px-2 py-1 text-xs text-popover-foreground shadow-md',
          'opacity-0 transition-opacity duration-150 group-hover:opacity-100',
          (props.side ?? 'top') === 'top' ? '-top-9' : 'top-full mt-2',
        )
      "
      role="tooltip"
    >
      {{ props.text }}
    </span>
  </span>
</template>
