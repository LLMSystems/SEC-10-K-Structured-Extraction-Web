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
  <div
    v-if="active"
    role="tabpanel"
    :class="cn('mt-2 focus-visible:outline-none', $props.class)"
  >
    <slot />
  </div>
</template>
