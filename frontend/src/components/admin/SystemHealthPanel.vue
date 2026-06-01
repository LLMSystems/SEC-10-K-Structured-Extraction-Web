<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { AlertCircle } from 'lucide-vue-next'
import Card from '@/components/ui/Card.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import { api } from '@/lib/api'
import type { JobAnalytics } from '@/types/api'

const data = ref<JobAnalytics | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    data.value = await api.adminJobStats()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '載入失敗'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const STATUS_META: Record<string, { label: string; color: string; bar: string }> = {
  done: { label: '完成', color: 'text-emerald-600 dark:text-emerald-500', bar: 'bg-emerald-500' },
  running: { label: '處理中', color: 'text-blue-600 dark:text-blue-400', bar: 'bg-blue-500' },
  pending: { label: '排隊中', color: 'text-amber-600 dark:text-amber-500', bar: 'bg-amber-500' },
  failed: { label: '失敗', color: 'text-destructive', bar: 'bg-destructive' },
}

const statuses = computed(() => {
  const counts = data.value?.status_counts ?? {}
  return Object.entries(counts).map(([status, count]) => ({
    status,
    count,
    meta: STATUS_META[status] ?? { label: status, color: 'text-muted-foreground', bar: 'bg-muted-foreground' },
  }))
})
const totalJobs = computed(() => statuses.value.reduce((s, x) => s + x.count, 0))

function fmtTime(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}
</script>

<template>
  <div v-if="loading" class="space-y-4">
    <Skeleton class="h-32 w-full" />
    <Skeleton class="h-48 w-full" />
  </div>

  <Card v-else-if="error" class="border-destructive/30 bg-destructive/5 p-4">
    <div class="flex items-center gap-2 text-sm text-destructive">
      <AlertCircle class="h-4 w-4" />{{ error }}
    </div>
  </Card>

  <div v-else-if="data" class="space-y-4">
    <!-- Job 狀態分佈 -->
    <Card class="p-4">
      <h3 class="mb-3 text-sm font-medium text-foreground">
        Job 狀態分佈
        <span class="ml-1 text-xs font-normal text-muted-foreground">(共 {{ totalJobs }})</span>
      </h3>
      <template v-if="totalJobs > 0">
        <div class="mb-3 flex h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            v-for="s in statuses"
            :key="s.status"
            :class="s.meta.bar"
            :style="{ width: `${(s.count / totalJobs) * 100}%` }"
          />
        </div>
        <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <div v-for="s in statuses" :key="s.status" class="flex items-center gap-2">
            <span :class="['h-2 w-2 rounded-sm', s.meta.bar]" />
            <span class="text-xs text-muted-foreground">{{ s.meta.label }}</span>
            <span class="ml-auto font-mono text-sm font-semibold" :class="s.meta.color">{{ s.count }}</span>
          </div>
        </div>
      </template>
      <p v-else class="text-xs text-muted-foreground">尚無 job 記錄</p>
    </Card>

    <!-- 最近失敗 -->
    <Card class="overflow-hidden">
      <div class="border-b border-border px-4 py-3 text-sm font-medium text-foreground">
        最近失敗的 Job
        <span class="ml-1 text-xs font-normal text-muted-foreground">
          ({{ data.recent_failures.length }})
        </span>
      </div>
      <div
        v-if="data.recent_failures.length === 0"
        class="px-4 py-10 text-center text-sm text-muted-foreground"
      >
        沒有失敗的 job 🎉
      </div>
      <ul v-else class="divide-y divide-border/60">
        <li v-for="job in data.recent_failures" :key="job.job_id" class="px-4 py-3">
          <div class="flex items-center justify-between gap-3">
            <span class="font-mono text-xs text-muted-foreground">
              {{ job.accession_number ?? job.job_id.slice(0, 8) }}
            </span>
            <span class="text-xs text-muted-foreground">{{ fmtTime(job.created_at) }}</span>
          </div>
          <p v-if="job.error_message" class="mt-1 line-clamp-2 text-xs text-destructive">
            {{ job.error_message }}
          </p>
        </li>
      </ul>
    </Card>
  </div>
</template>
