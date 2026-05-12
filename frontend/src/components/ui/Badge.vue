<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

type Variant = 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'info'

const props = withDefaults(defineProps<{ variant?: Variant; class?: string }>(), {
  variant: 'default',
})

const variants: Record<Variant, string> = {
  default: 'bg-primary/10 text-primary border border-primary/20',
  secondary: 'bg-secondary text-secondary-foreground border border-border',
  outline: 'border border-border text-foreground',
  success:
    'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20',
  warning:
    'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20',
  info: 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border border-blue-500/20',
}

const classes = computed(() =>
  cn(
    'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium leading-none',
    variants[props.variant],
    props.class,
  ),
)
</script>

<template>
  <span :class="classes"><slot /></span>
</template>
