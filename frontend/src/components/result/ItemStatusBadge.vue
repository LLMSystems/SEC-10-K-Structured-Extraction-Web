<script setup lang="ts">
import { computed } from 'vue'
import { AlertCircle, Ban, CheckCircle2, ExternalLink, Minus } from 'lucide-vue-next'
import type { ItemStatus } from '@/types/api'

const props = defineProps<{ status: ItemStatus; small?: boolean }>()

const config = computed(() => {
  switch (props.status) {
    case 'extracted':
      return { icon: CheckCircle2, color: 'text-emerald-600 dark:text-emerald-500', label: '已解析' }
    case 'incorporated_by_reference':
      return { icon: ExternalLink, color: 'text-blue-500', label: '以引用方式揭露' }
    case 'not_applicable':
      return { icon: Minus, color: 'text-zinc-400 dark:text-zinc-500', label: '不適用' }
    case 'reserved':
      return { icon: Ban, color: 'text-zinc-400 dark:text-zinc-500', label: 'SEC 保留' }
    case 'missing':
      return { icon: AlertCircle, color: 'text-amber-500', label: '未找到' }
    default:
      return { icon: AlertCircle, color: 'text-muted-foreground', label: props.status }
  }
})
</script>

<template>
  <component
    :is="config.icon"
    :class="[config.color, props.small ? 'h-3 w-3' : 'h-3.5 w-3.5']"
    :aria-label="config.label"
  />
</template>
