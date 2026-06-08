<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { AlertCircle, ArrowLeft, CheckCircle2, Download } from 'lucide-vue-next'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import ItemStatusBadge from '@/components/result/ItemStatusBadge.vue'
import ItemDetailDrawer from '@/components/admin/ItemDetailDrawer.vue'
import { api } from '@/lib/api'
import { statusLabel } from '@/lib/statusLabels'
import { flagLabel, scoreColor, severityClasses } from '@/lib/flagLabels'
import type { FilingItem, FilingOutput, ValidationFlag } from '@/types/api'

const props = defineProps<{ accession: string }>()
const router = useRouter()

const filing = ref<FilingOutput | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    filing.value = await api.getFiling(props.accession, { stripContent: true })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '載入失敗'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.accession, load)

const quality = computed(() => filing.value?.quality ?? null)

// 文件級 flags（item_number 為 null）與逐 item flags 分開呈現
const allFlags = computed<ValidationFlag[]>(() => quality.value?.flags ?? [])
const docFlags = computed(() => allFlags.value.filter((f) => !f.item_number))
const itemLevelFlags = computed(() => allFlags.value.filter((f) => f.item_number))
const itemFlagMap = computed(() => {
  const map: Record<string, ValidationFlag[]> = {}
  for (const f of itemLevelFlags.value) {
    if (f.item_number) (map[f.item_number] ??= []).push(f)
  }
  return map
})

// 點列 → 右側抽屜看該 item 的完整內容；關閉後保留 selectedItem 讓滑出動畫完整。
const selectedItem = ref<FilingItem | null>(null)
const drawerOpen = ref(false)
const selectedItemFlags = computed(() =>
  selectedItem.value ? itemFlagMap.value[selectedItem.value.item_number] ?? [] : [],
)

function openItem(item: FilingItem) {
  selectedItem.value = item
  drawerOpen.value = true
}

function rowHighlight(itemNumber: string): string {
  const flags = itemFlagMap.value[itemNumber] ?? []
  if (flags.some((f) => f.severity === 'error')) return 'bg-destructive/5'
  if (flags.some((f) => f.severity === 'warning')) return 'bg-amber-500/5'
  return ''
}

function downloadJson() {
  if (!filing.value) return
  const blob = new Blob([JSON.stringify(filing.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.accession}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function fmtConf(c: number | null): string {
  return c == null ? '—' : c.toFixed(2)
}
</script>

<template>
  <div class="mx-auto max-w-screen-xl px-4 py-6">
    <Button variant="ghost" size="sm" class="mb-4 -ml-2" @click="router.push('/admin')">
      <ArrowLeft class="h-4 w-4" />
      返回後台
    </Button>

    <!-- Error -->
    <Card v-if="error" class="border-destructive/30 bg-destructive/5 p-4">
      <div class="flex items-center gap-2 text-sm text-destructive">
        <AlertCircle class="h-4 w-4" />
        {{ error }}
      </div>
    </Card>

    <!-- Loading -->
    <div v-else-if="loading" class="space-y-4">
      <Skeleton class="h-24 w-full" />
      <Skeleton class="h-40 w-full" />
      <Skeleton class="h-64 w-full" />
    </div>

    <template v-else-if="filing">
      <!-- Header summary -->
      <div class="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-xl font-semibold tracking-tight text-foreground">
            {{ filing.filing_info.company_name ?? '—' }}
          </h1>
          <p class="mt-1 font-mono text-xs text-muted-foreground">
            {{ filing.filing_info.accession_number }} ·
            FY {{ filing.filing_info.fiscal_year_end ?? '—' }} ·
            {{ filing.filing_info.filer_category ?? '—' }}
          </p>
        </div>
        <Button variant="outline" size="sm" @click="downloadJson">
          <Download class="h-3.5 w-3.5" />
          下載 JSON
        </Button>
      </div>

      <!-- Quality summary -->
      <Card v-if="quality" class="mb-5 p-4">
        <div class="flex flex-wrap items-center gap-x-8 gap-y-3">
          <div>
            <div class="text-xs text-muted-foreground">分數</div>
            <div class="text-2xl font-semibold tabular-nums" :class="scoreColor(quality.score)">
              {{ quality.score.toFixed(2) }}
            </div>
          </div>
          <div>
            <div class="text-xs text-muted-foreground">狀態</div>
            <div class="mt-1 flex items-center gap-1.5 text-sm font-medium">
              <CheckCircle2 v-if="quality.is_valid" class="h-4 w-4 text-emerald-500" />
              <AlertCircle v-else class="h-4 w-4 text-destructive" />
              {{ quality.is_valid ? '有效' : '無效' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-muted-foreground">Error / Warning / Info</div>
            <div class="mt-1 text-sm font-medium tabular-nums">
              <span class="text-destructive">{{ quality.counts.error ?? 0 }}</span> /
              <span class="text-amber-600 dark:text-amber-500">{{ quality.counts.warning ?? 0 }}</span> /
              <span class="text-blue-600 dark:text-blue-400">{{ quality.counts.info ?? 0 }}</span>
            </div>
          </div>
          <div>
            <div class="text-xs text-muted-foreground">Parser</div>
            <div class="mt-1 font-mono text-xs text-foreground">{{ quality.parser_name }}</div>
          </div>
          <div>
            <div class="text-xs text-muted-foreground">覆蓋率 / 找到</div>
            <div class="mt-1 text-sm font-medium tabular-nums">
              {{ (quality.coverage_ratio * 100).toFixed(1) }}% ·
              {{ quality.found_item_count }}/{{ quality.expected_item_count }}
            </div>
          </div>
        </div>
        <div
          v-if="quality.missing_required_items.length"
          class="mt-3 border-t border-border pt-3 text-xs text-destructive"
        >
          缺失必要 Item：{{ quality.missing_required_items.join('、') }}
        </div>
      </Card>

      <Card v-else class="mb-5 p-4 text-sm text-muted-foreground">
        此 filing 為舊版結果，尚無品質報告（重新解析後即會產生）。
      </Card>

      <!-- Flags -->
      <Card v-if="quality && quality.flags.length" class="mb-5 overflow-hidden">
        <div class="border-b border-border px-4 py-3 text-sm font-medium text-foreground">
          驗證問題 ({{ quality.flags.length }})
        </div>
        <ul class="divide-y divide-border/60">
          <li
            v-for="(f, i) in [...docFlags, ...itemLevelFlags]"
            :key="i"
            class="flex items-start gap-3 px-4 py-2.5"
          >
            <span
              class="mt-0.5 inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[11px] font-medium leading-none"
              :class="severityClasses(f.severity)"
            >
              {{ f.severity }}
            </span>
            <div class="min-w-0">
              <div class="flex items-center gap-2 text-sm">
                <span class="font-medium text-foreground">{{ flagLabel(f.code) }}</span>
                <span v-if="f.item_number" class="font-mono text-xs text-muted-foreground">
                  Item {{ f.item_number }}
                </span>
                <span class="font-mono text-[10px] text-muted-foreground/60">{{ f.code }}</span>
              </div>
              <p class="mt-0.5 text-xs text-muted-foreground">{{ f.message }}</p>
            </div>
          </li>
        </ul>
      </Card>

      <!-- Items table -->
      <Card class="overflow-hidden">
        <div class="flex items-center justify-between border-b border-border px-4 py-3">
          <span class="text-sm font-medium text-foreground">Items ({{ filing.items.length }})</span>
          <span class="text-xs text-muted-foreground">點任一列查看內容</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border text-left text-xs text-muted-foreground">
                <th class="px-4 py-2 font-medium">Item</th>
                <th class="px-4 py-2 font-medium">標題</th>
                <th class="px-4 py-2 font-medium">Status</th>
                <th class="px-4 py-2 text-center font-medium">信心</th>
                <th class="px-4 py-2 font-medium">Range</th>
                <th class="px-4 py-2 font-medium">Flags</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in filing.items"
                :key="item.item_number"
                class="cursor-pointer border-b border-border/60 transition-colors hover:bg-accent/50"
                :class="rowHighlight(item.item_number)"
                @click="openItem(item)"
              >
                <td class="px-4 py-2.5 font-mono text-xs font-medium text-foreground">
                  {{ item.item_number }}
                </td>
                <td class="max-w-[20rem] truncate px-4 py-2.5 text-foreground">
                  {{ item.item_title }}
                </td>
                <td class="px-4 py-2.5">
                  <span class="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                    <ItemStatusBadge :status="item.status" small />
                    {{ statusLabel(item.status) }}
                  </span>
                </td>
                <td class="px-4 py-2.5 text-center tabular-nums text-muted-foreground">
                  {{ fmtConf(item.confidence) }}
                </td>
                <td class="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                  {{ item.char_range ? `${item.char_range[0]}–${item.char_range[1]}` : '—' }}
                </td>
                <td class="px-4 py-2.5">
                  <div v-if="item.flag_codes.length" class="flex flex-wrap gap-1">
                    <span
                      v-for="code in item.flag_codes"
                      :key="code"
                      class="rounded border border-border bg-muted/50 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                    >
                      {{ flagLabel(code) }}
                    </span>
                  </div>
                  <span v-else class="text-xs text-muted-foreground/50">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </template>

    <ItemDetailDrawer
      :open="drawerOpen"
      :item="selectedItem"
      :flags="selectedItemFlags"
      :accession="props.accession"
      @close="drawerOpen = false"
    />
  </div>
</template>
