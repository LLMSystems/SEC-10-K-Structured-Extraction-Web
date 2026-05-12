<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { AlertCircle, CheckCircle2, Zap } from 'lucide-vue-next'
import MonoText from '@/components/common/MonoText.vue'
import { useJobStore } from '@/stores/job'

const props = defineProps<{ jobId: string | null }>()

const job = useJobStore()

const STEPS = [
  { key: 'fetch', label: '下載 HTML' },
  { key: 'preprocess', label: '預處理' },
  { key: 'parse', label: '解析項目' },
  { key: 'postprocess', label: '後處理' },
] as const

const stepIndex = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => {
    if (job.phase === 'done' || job.phase === 'cache_hit') {
      stepIndex.value = STEPS.length
      return
    }
    if (job.phase === 'error') return
    stepIndex.value = Math.min(stepIndex.value + 1, STEPS.length - 1)
  }, 350)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

const isCacheHit = computed(() => job.cacheHit && job.phase !== 'error')
const isError = computed(() => job.phase === 'error')
const progressPercent = computed(() => {
  if (job.phase === 'done' || job.phase === 'cache_hit') return 100
  if (job.phase === 'error') return 100
  return Math.min(((stepIndex.value + 1) / STEPS.length) * 100, 90)
})
</script>

<template>
  <div
    class="rounded-xl border border-border bg-card p-5 shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-300"
  >
    <div v-if="isError" class="flex items-start gap-3">
      <AlertCircle class="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
      <div class="flex-1">
        <p class="font-medium text-foreground">解析失敗</p>
        <p class="mt-1 text-sm text-muted-foreground">{{ job.error }}</p>
      </div>
    </div>

    <template v-else>
      <div class="flex items-center gap-2 text-sm">
        <CheckCircle2 v-if="props.jobId" class="h-4 w-4 text-emerald-500" />
        <span class="text-muted-foreground">Job 已送出</span>
        <MonoText v-if="props.jobId" class="ml-auto text-xs text-muted-foreground">
          {{ props.jobId.slice(0, 8) }}…
        </MonoText>
      </div>

      <div v-if="isCacheHit" class="mt-4 flex items-center gap-2.5 text-sm">
        <Zap class="h-4 w-4 animate-pulse text-amber-500" />
        <span class="font-medium text-foreground">快取命中 — 立即取得結果</span>
      </div>

      <div v-else class="mt-4">
        <div class="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            class="h-full rounded-full bg-primary transition-all duration-500 ease-out"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>

        <div class="mt-4 grid grid-cols-4 gap-2">
          <div
            v-for="(step, i) in STEPS"
            :key="step.key"
            class="flex flex-col items-start gap-1.5"
          >
            <div class="flex items-center gap-1.5">
              <span
                :class="[
                  'h-1.5 w-1.5 rounded-full transition-colors',
                  i <= stepIndex ? 'bg-primary' : 'bg-border',
                ]"
              />
              <span
                :class="[
                  'text-[11px] font-medium tracking-wider transition-colors',
                  i <= stepIndex ? 'text-foreground' : 'text-muted-foreground',
                ]"
              >
                {{ step.label }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
