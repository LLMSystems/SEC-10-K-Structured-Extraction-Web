<script setup lang="ts">
import { computed } from 'vue'
import { AlertCircle, CheckCircle2, Info, X, Zap } from 'lucide-vue-next'
import { useToastStore, type ToastVariant } from '@/stores/toast'

const store = useToastStore()

const variantStyles: Record<ToastVariant, string> = {
  default: 'border-border bg-popover',
  success: 'border-emerald-500/30 bg-popover',
  error: 'border-destructive/40 bg-popover',
  info: 'border-blue-500/30 bg-popover',
}

function iconFor(v: ToastVariant) {
  if (v === 'success') return CheckCircle2
  if (v === 'error') return AlertCircle
  if (v === 'info') return Info
  return Zap
}

const list = computed(() => store.toasts)
</script>

<template>
  <div
    aria-live="polite"
    class="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-full max-w-sm flex-col gap-2"
  >
    <transition-group
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0 translate-x-2"
    >
      <div
        v-for="t in list"
        :key="t.id"
        :class="[
          'pointer-events-auto flex items-start gap-3 rounded-lg border p-3 shadow-lg',
          variantStyles[t.variant],
        ]"
      >
        <component
          :is="iconFor(t.variant)"
          :class="[
            'mt-0.5 h-4 w-4 shrink-0',
            t.variant === 'success'
              ? 'text-emerald-500'
              : t.variant === 'error'
                ? 'text-destructive'
                : t.variant === 'info'
                  ? 'text-blue-500'
                  : 'text-primary',
          ]"
        />
        <div class="flex-1 text-sm">
          <p class="font-medium text-foreground">{{ t.title }}</p>
          <p v-if="t.description" class="mt-0.5 text-muted-foreground">{{ t.description }}</p>
        </div>
        <button
          class="text-muted-foreground transition-colors hover:text-foreground"
          @click="store.dismiss(t.id)"
          aria-label="Dismiss"
        >
          <X class="h-3.5 w-3.5" />
        </button>
      </div>
    </transition-group>
  </div>
</template>
