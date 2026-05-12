<script setup lang="ts">
import { computed } from 'vue'
import type { FilingTiming } from '@/types/api'

const props = defineProps<{ timing: FilingTiming }>()

const segments = computed(() => [
  { key: 'fetch', label: '下載 HTML', value: props.timing.fetch_html_sec, color: 'bg-blue-500' },
  {
    key: 'preprocess',
    label: '預處理',
    value: props.timing.preprocess_sec,
    color: 'bg-emerald-500',
  },
  { key: 'parse', label: '解析', value: props.timing.parse_sec, color: 'bg-amber-500' },
  {
    key: 'postprocess',
    label: '後處理',
    value: props.timing.postprocess_sec,
    color: 'bg-purple-500',
  },
])

const total = computed(() => segments.value.reduce((sum, s) => sum + s.value, 0))

function fmt(n: number) {
  return n < 0.01 ? '<0.01s' : `${n.toFixed(2)}s`
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-baseline justify-between">
      <span class="text-xs font-medium tracking-wider text-muted-foreground">
        處理時間
      </span>
      <span class="font-mono text-sm font-semibold text-foreground">
        {{ fmt(total) }}
      </span>
    </div>

    <div class="flex h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div
        v-for="seg in segments"
        :key="seg.key"
        :class="seg.color"
        :style="{ width: `${total > 0 ? (seg.value / total) * 100 : 0}%` }"
      />
    </div>

    <div class="space-y-1.5">
      <div
        v-for="seg in segments"
        :key="seg.key"
        class="flex items-center justify-between text-xs"
      >
        <div class="flex items-center gap-2">
          <span :class="['h-2 w-2 shrink-0 rounded-sm', seg.color]" />
          <span class="text-muted-foreground">{{ seg.label }}</span>
        </div>
        <span class="font-mono text-foreground">{{ fmt(seg.value) }}</span>
      </div>
    </div>
  </div>
</template>
