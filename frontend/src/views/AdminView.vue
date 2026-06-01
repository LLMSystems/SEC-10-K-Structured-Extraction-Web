<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  FileWarning,
  Gauge,
  RefreshCw,
} from 'lucide-vue-next'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import Tabs from '@/components/ui/Tabs.vue'
import TabsList from '@/components/ui/TabsList.vue'
import TabsTrigger from '@/components/ui/TabsTrigger.vue'
import TabsContent from '@/components/ui/TabsContent.vue'
import FlagAnalyticsPanel from '@/components/admin/FlagAnalyticsPanel.vue'
import SystemHealthPanel from '@/components/admin/SystemHealthPanel.vue'
import { api } from '@/lib/api'
import { scoreColor } from '@/lib/flagLabels'
import type {
  AdminStats,
  FilingFilter,
  FilingListItem,
  FilingSort,
} from '@/types/api'

const router = useRouter()

const stats = ref<AdminStats | null>(null)
const filings = ref<FilingListItem[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

const sort = ref<FilingSort>('score_asc')
const only = ref<FilingFilter>('all')
const activeTab = ref('queue')

const validRate = computed(() => {
  if (!stats.value || stats.value.total_filings === 0) return null
  return stats.value.valid_count / stats.value.total_filings
})

async function load() {
  loading.value = true
  error.value = null
  try {
    const [s, list] = await Promise.all([
      api.adminStats(),
      api.adminFilings({ sort: sort.value, only: only.value, limit: 100 }),
    ])
    stats.value = s
    filings.value = list.items
    total.value = list.total
  } catch (e) {
    error.value = e instanceof Error ? e.message : '載入失敗'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch([sort, only], load)

function openFiling(acc: string) {
  router.push({ name: 'admin-filing', params: { accession: acc } })
}

function fmtScore(s: number | null): string {
  return s == null ? '—' : s.toFixed(2)
}
function fmtMs(ms: number | null): string {
  if (ms == null) return '—'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}
function fmtTime(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

const filterOptions: { value: FilingFilter; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'errors', label: '有 Error' },
  { value: 'invalid', label: '無效' },
]
const sortOptions: { value: FilingSort; label: string }[] = [
  { value: 'score_asc', label: '分數低→高' },
  { value: 'score_desc', label: '分數高→低' },
  { value: 'recent', label: '最近處理' },
]
</script>

<template>
  <div class="mx-auto max-w-screen-2xl px-4 py-6">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold tracking-tight text-foreground">
          解析品質後台
        </h1>
        <p class="mt-1 text-sm text-muted-foreground">
          監控解析品質、分流待審 filing、追蹤錯誤來源
        </p>
      </div>
      <Button variant="outline" size="sm" :disabled="loading" @click="load">
        <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': loading }" />
        重新整理
      </Button>
    </div>

    <!-- Error -->
    <Card v-if="error" class="mb-6 border-destructive/30 bg-destructive/5 p-4">
      <div class="flex items-center gap-2 text-sm text-destructive">
        <AlertCircle class="h-4 w-4" />
        {{ error }}
      </div>
    </Card>

    <!-- KPI cards -->
    <div class="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Card class="p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs text-muted-foreground">總處理數</span>
          <Gauge class="h-4 w-4 text-muted-foreground" />
        </div>
        <Skeleton v-if="loading && !stats" class="mt-2 h-7 w-16" />
        <div v-else class="mt-1 text-2xl font-semibold tabular-nums">
          {{ stats?.total_filings ?? 0 }}
        </div>
      </Card>

      <Card class="p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs text-muted-foreground">有效率</span>
          <CheckCircle2 class="h-4 w-4 text-emerald-500" />
        </div>
        <Skeleton v-if="loading && !stats" class="mt-2 h-7 w-16" />
        <div v-else class="mt-1 text-2xl font-semibold tabular-nums">
          {{ validRate == null ? '—' : `${(validRate * 100).toFixed(0)}%` }}
          <span class="text-xs font-normal text-muted-foreground">
            ({{ stats?.valid_count ?? 0 }}/{{ stats?.total_filings ?? 0 }})
          </span>
        </div>
      </Card>

      <Card class="p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs text-muted-foreground">平均分數</span>
          <Gauge class="h-4 w-4 text-muted-foreground" />
        </div>
        <Skeleton v-if="loading && !stats" class="mt-2 h-7 w-16" />
        <div
          v-else
          class="mt-1 text-2xl font-semibold tabular-nums"
          :class="scoreColor(stats?.avg_score ?? null)"
        >
          {{ fmtScore(stats?.avg_score ?? null) }}
        </div>
      </Card>

      <Card class="p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs text-muted-foreground">需注意</span>
          <FileWarning class="h-4 w-4 text-amber-500" />
        </div>
        <Skeleton v-if="loading && !stats" class="mt-2 h-7 w-16" />
        <div v-else class="mt-1 flex items-baseline gap-3">
          <span class="flex items-center gap-1 text-lg font-semibold text-destructive">
            <AlertCircle class="h-4 w-4" />{{ stats?.error_filings ?? 0 }}
          </span>
          <span class="flex items-center gap-1 text-lg font-semibold text-amber-600 dark:text-amber-500">
            <AlertTriangle class="h-4 w-4" />{{ stats?.warning_filings ?? 0 }}
          </span>
          <span class="text-xs text-muted-foreground">
            job 失敗 {{ stats?.failed_jobs ?? 0 }}
          </span>
        </div>
      </Card>
    </div>

    <!-- Tabs: 待審佇列 / 規則分析 / 系統健康 -->
    <Tabs v-model="activeTab">
      <TabsList class="mb-4">
        <TabsTrigger value="queue">待審佇列</TabsTrigger>
        <TabsTrigger value="analytics">規則分析</TabsTrigger>
        <TabsTrigger value="system">系統健康</TabsTrigger>
      </TabsList>

      <!-- ② 待審佇列 -->
      <TabsContent value="queue">
        <Card class="overflow-hidden">
      <div class="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <h2 class="text-sm font-medium text-foreground">
          待審佇列
          <span class="ml-1 text-xs font-normal text-muted-foreground">({{ total }})</span>
        </h2>
        <div class="flex items-center gap-2">
          <div class="flex rounded-md border border-border p-0.5">
            <button
              v-for="opt in filterOptions"
              :key="opt.value"
              class="rounded px-2.5 py-1 text-xs font-medium transition-colors"
              :class="only === opt.value ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
              @click="only = opt.value"
            >
              {{ opt.label }}
            </button>
          </div>
          <select
            v-model="sort"
            class="h-8 rounded-md border border-border bg-background px-2 text-xs text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
          >
            <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-2 p-4">
        <Skeleton v-for="i in 6" :key="i" class="h-10 w-full" />
      </div>

      <!-- Empty -->
      <div
        v-else-if="filings.length === 0"
        class="px-4 py-16 text-center text-sm text-muted-foreground"
      >
        尚無符合條件的 filing
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border text-left text-xs text-muted-foreground">
              <th class="px-4 py-2 font-medium">分數</th>
              <th class="px-4 py-2 font-medium">公司</th>
              <th class="px-4 py-2 font-medium">Accession</th>
              <th class="px-4 py-2 text-center font-medium">有效</th>
              <th class="px-4 py-2 text-center font-medium">Err</th>
              <th class="px-4 py-2 text-center font-medium">Warn</th>
              <th class="px-4 py-2 font-medium">Parser</th>
              <th class="px-4 py-2 font-medium">耗時</th>
              <th class="px-4 py-2 font-medium">時間</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="f in filings"
              :key="f.accession_number"
              class="cursor-pointer border-b border-border/60 transition-colors hover:bg-accent/50"
              @click="openFiling(f.accession_number)"
            >
              <td class="px-4 py-2.5 font-semibold tabular-nums" :class="scoreColor(f.quality_score)">
                {{ fmtScore(f.quality_score) }}
              </td>
              <td class="max-w-[16rem] truncate px-4 py-2.5 font-medium text-foreground">
                {{ f.company_name ?? '—' }}
              </td>
              <td class="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                {{ f.accession_number }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <CheckCircle2 v-if="f.quality_valid === true" class="mx-auto h-4 w-4 text-emerald-500" />
                <AlertCircle v-else-if="f.quality_valid === false" class="mx-auto h-4 w-4 text-destructive" />
                <span v-else class="text-muted-foreground">—</span>
              </td>
              <td class="px-4 py-2.5 text-center tabular-nums" :class="(f.quality_errors ?? 0) > 0 ? 'font-semibold text-destructive' : 'text-muted-foreground'">
                {{ f.quality_errors ?? 0 }}
              </td>
              <td class="px-4 py-2.5 text-center tabular-nums" :class="(f.quality_warnings ?? 0) > 0 ? 'font-semibold text-amber-600 dark:text-amber-500' : 'text-muted-foreground'">
                {{ f.quality_warnings ?? 0 }}
              </td>
              <td class="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                {{ f.parser_name ?? '—' }}
              </td>
              <td class="px-4 py-2.5 tabular-nums text-muted-foreground">
                {{ fmtMs(f.processing_ms) }}
              </td>
              <td class="px-4 py-2.5 text-xs text-muted-foreground">
                {{ fmtTime(f.fetched_at) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
        </Card>
      </TabsContent>

      <!-- ④ 規則分析 -->
      <TabsContent value="analytics">
        <FlagAnalyticsPanel />
      </TabsContent>

      <!-- ⑤ 系統健康 -->
      <TabsContent value="system">
        <SystemHealthPanel />
      </TabsContent>
    </Tabs>
  </div>
</template>
