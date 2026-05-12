import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastVariant = 'default' | 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  title: string
  description?: string
  variant: ToastVariant
  duration: number
}

let nextId = 1

export const useToastStore = defineStore('toast', () => {
  const toasts = ref<ToastItem[]>([])

  function push(opts: {
    title: string
    description?: string
    variant?: ToastVariant
    duration?: number
  }) {
    const item: ToastItem = {
      id: nextId++,
      title: opts.title,
      description: opts.description,
      variant: opts.variant ?? 'default',
      duration: opts.duration ?? 3500,
    }
    toasts.value = [...toasts.value, item]
    setTimeout(() => dismiss(item.id), item.duration)
  }

  function dismiss(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  return { toasts, push, dismiss }
})
