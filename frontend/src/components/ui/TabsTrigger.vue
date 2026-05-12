<script setup lang="ts">
import { computed, inject, type Ref } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{ value: string; class?: string }>()

const ctx = inject<{ value: Readonly<Ref<string>>; setValue: (v: string) => void } | null>(
  'tabs',
  null,
)
const active = computed(() => ctx?.value.value === props.value)
</script>

<template>
  <button
    type="button"
    role="tab"
    :aria-selected="active"
    @click="ctx?.setValue(props.value)"
    :class="
      cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium transition-all',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40',
        active
          ? 'bg-background text-foreground shadow-sm'
          : 'text-muted-foreground hover:text-foreground',
        $props.class,
      )
    "
  >
    <slot />
  </button>
</template>
