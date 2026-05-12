<script setup lang="ts">
import { cn } from '@/lib/utils'
const props = withDefaults(
  defineProps<{ orientation?: 'horizontal' | 'vertical'; class?: string }>(),
  { orientation: 'horizontal' },
)
</script>

<template>
  <div
    :class="
      cn(
        'shrink-0 bg-border',
        props.orientation === 'vertical' ? 'h-full w-px' : 'h-px w-full',
        props.class,
      )
    "
    role="separator"
  />
</template>
