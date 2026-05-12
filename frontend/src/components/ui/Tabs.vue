<script setup lang="ts">
import { provide, readonly, ref, watch } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{ modelValue: string; class?: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const current = ref(props.modelValue)
watch(
  () => props.modelValue,
  (v) => (current.value = v),
)

function setValue(v: string) {
  current.value = v
  emit('update:modelValue', v)
}

provide('tabs', { value: readonly(current), setValue })
</script>

<template>
  <div :class="cn('w-full', props.class)"><slot /></div>
</template>
