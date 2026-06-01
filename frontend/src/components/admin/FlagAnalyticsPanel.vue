<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { AlertCircle } from 'lucide-vue-next'
import Card from '@/components/ui/Card.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import { api } from '@/lib/api'
import { flagLabel, scoreColor } from '@/lib/flagLabels'
import type { FlagAnalytics } from '@/types/api'

const data = ref<FlagAnalytics | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    data.value = await api.adminFlagStats()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '載入失敗'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const maxCode = computed(() =>
  Math.max(1, ...(data.value?.by_code.map((c) => c.count) ?? [1])),
)
const maxItem = computed(() =>
  Math.max(1, ...(data.value?.by_item.map((c) => c.count) ?? [1])),
)

function severityBar(severity: string): string {
  if (severity === 'error') return 'bg-destructive'
  if (severity === 'warning') return 'bg-amber-500'
  return 'bg-blue-500'
}

const timingSegments = computed(() => {
  const t = data.value?.timing
  if (!t) return []
  return [
    { label: '下載', value: t.fetch_html_sec, color: 'bg-blue-500' },
    { label: '預處理', value: t.preprocess_sec, color: 'bg-emerald-500' },
    { label: '解析', value: t.parse_sec, color: 'bg-amber-500' },
    { label: '後處理', value: t.postprocess_sec, color: 'bg-purple-500' },
  ]
})
const timingTotal = computed(() =>
  timingSegments.value.reduce((s, x) => s + x.value, 0),
)
</script>

<template>
  <div v-if="loading" class="space-y-4">
    <Skeleton class="h-48 w-full" />
    <Skeleton class="h-48 w-full" />
  </div>

  <Card v-else-if="error" class="border-destructive/30 bg-destructive/5 p-4">
    <div class="flex items-center gap-2 text-sm text-destructive">
      <AlertCircle class="h-4 w-4" />{{ error }}
    </div>
  </Card>

  <div
    v-else-if="data && data.total_flags === 0 && data.by_parser.length === 0"
    class="px-4 py-16 text-center text-sm text-muted-foreground"
  >
    尚無資料，先處理幾份 filing 後即會出現分析。
  </div>

  <div v-else-if="data" class="grid gap-4 lg:grid-cols-2">
    <!-- Flag code 頻率 -->
    <Card class="p-4">
      <h3 class="mb-3 text-sm font-medium text-foreground">
        規則觸發頻率
        <span class="ml-1 text-xs font-normal text-muted-foreground">
          (共 {{ data.total_flags }} 筆)
        </span>
      </h3>
      <div v-if="data.by_code.length" class="space-y-2">
        <div v-for="c in data.by_code" :key="c.code">
          <div class="mb-0.5 flex items-center justify-between text-xs">
            <span class="text-foreground">{{ flagLabel(c.code) }}</span>
            <span class="font-mono text-muted-foreground">{{ c.count }}</span>
          </div>
          <div class="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              :class="severityBar(c.severity)"
              :style="{ width: `${(c.count / maxCode) * 100}%` }"
              class="h-full"
            />
          </div>
        </div>
      </div>
      <p v-else class="text-xs text-muted-foreground">尚無觸發任何規則 🎉</p>
    </Card>

    <!-- 問題集中的 Item -->
    <Card class="p-4">
      <h3 class="mb-3 text-sm font-medium text-foreground">問題集中的 Item</h3>
      <div v-if="data.by_item.length" class="space-y-2">
        <div v-for="it in data.by_item" :key="it.item_number">
          <div class="mb-0.5 flex items-center justify-between text-xs">
            <span class="font-mono text-foreground">Item {{ it.item_number }}</span>
            <span class="font-mono text-muted-foreground">{{ it.count }}</span>
          </div>
          <div class="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              class="h-full bg-primary"
              :style="{ width: `${(it.count / maxItem) * 100}%` }"
            />
          </div>
        </div>
      </div>
      <p v-else class="text-xs text-muted-foreground">無逐 Item 問題</p>
    </Card>

    <!-- Parser 彙總 -->
    <Card class="p-4">
      <h3 class="mb-3 text-sm font-medium text-foreground">各 Parser 表現</h3>
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs text-muted-foreground">
            <th class="pb-2 font-medium">Parser</th>
            <th class="pb-2 text-right font-medium">份數</th>
            <th class="pb-2 text-right font-medium">Err</th>
            <th class="pb-2 text-right font-medium">Warn</th>
            <th class="pb-2 text-right font-medium">⌀分數</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in data.by_parser" :key="p.parser_name ?? 'none'" class="border-t border-border/60">
            <td class="py-1.5 font-mono text-xs text-foreground">{{ p.parser_name ?? '—' }}</td>
            <td class="py-1.5 text-right tabular-nums text-muted-foreground">{{ p.filings }}</td>
            <td class="py-1.5 text-right tabular-nums" :class="p.errors > 0 ? 'text-destructive' : 'text-muted-foreground'">{{ p.errors }}</td>
            <td class="py-1.5 text-right tabular-nums" :class="p.warnings > 0 ? 'text-amber-600 dark:text-amber-500' : 'text-muted-foreground'">{{ p.warnings }}</td>
            <td class="py-1.5 text-right font-semibold tabular-nums" :class="scoreColor(p.avg_score)">
              {{ p.avg_score == null ? '—' : p.avg_score.toFixed(2) }}
            </td>
          </tr>
        </tbody>
      </table>
    </Card>

    <!-- 平均階段耗時 -->
    <Card class="p-4">
      <h3 class="mb-3 text-sm font-medium text-foreground">平均各階段耗時</h3>
      <template v-if="data.timing">
        <div class="mb-3 flex h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            v-for="seg in timingSegments"
            :key="seg.label"
            :class="seg.color"
            :style="{ width: `${timingTotal > 0 ? (seg.value / timingTotal) * 100 : 0}%` }"
          />
        </div>
        <div class="space-y-1.5">
          <div
            v-for="seg in timingSegments"
            :key="seg.label"
            class="flex items-center justify-between text-xs"
          >
            <span class="flex items-center gap-2">
              <span :class="['h-2 w-2 rounded-sm', seg.color]" />
              <span class="text-muted-foreground">{{ seg.label }}</span>
            </span>
            <span class="font-mono text-foreground">{{ seg.value.toFixed(2) }}s</span>
          </div>
        </div>
      </template>
      <p v-else class="text-xs text-muted-foreground">尚無耗時資料</p>
    </Card>
  </div>
</template>
