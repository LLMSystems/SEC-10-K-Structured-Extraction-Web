<script setup lang="ts">
import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    placeholder?: string
    type?: string
    disabled?: boolean
    mono?: boolean
    autocomplete?: string
    spellcheck?: boolean
  }>(),
  { type: 'text', disabled: false, mono: false, spellcheck: false },
)

const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
}
</script>

<template>
  <input
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :autocomplete="autocomplete"
    :spellcheck="spellcheck"
    @input="onInput"
    :class="
      cn(
        'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
        'placeholder:text-muted-foreground transition-shadow',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:border-primary/60',
        'disabled:cursor-not-allowed disabled:opacity-50',
        props.mono && 'font-mono tracking-tight',
      )
    "
  />
</template>
