<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { AlertCircle, Ban, ExternalLink, Minus } from 'lucide-vue-next'
import Drawer from '@/components/ui/Drawer.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import ItemStatusBadge from '@/components/result/ItemStatusBadge.vue'
import { api } from '@/lib/api'
import { renderMarkdown } from '@/lib/markdown'
import { statusLabel } from '@/lib/statusLabels'
import { flagLabel, severityClasses } from '@/lib/flagLabels'
import type { FilingItem, ValidationFlag } from '@/types/api'

const props = defineProps<{
  open: boolean
  item: FilingItem | null
  flags: ValidationFlag[]
  accession?: string
}>()
const emit = defineEmits<{ (e: 'close'): void }>()

// fetchedContent holds content_text retrieved from the lazy-load API call.
// It is reset whenever the selected item changes.
const fetchedContent = ref<string | null>(null)
const isFetchingContent = ref(false)
const fetchError = ref<string | null>(null)

const renderedHtml = ref('')
const isRendering = ref(false)

// When item changes, clear previously fetched content.
watch(
  () => props.item?.item_number,
  () => {
    fetchedContent.value = null
    fetchError.value = null
    isFetchingContent.value = false
  },
)

// When the drawer opens (or the selected item changes while open), lazy-fetch
// content_text if the item needs content but it was stripped from the main payload.
watch(
  [() => props.open, () => props.item] as const,
  async ([open, item]) => {
    if (!open || !item || !props.accession) return
    const needsContent =
      item.status === 'extracted' || item.status === 'incorporated_by_reference'
    if (!needsContent) return
    // Already have content either inline or from a previous fetch.
    if (item.content_text !== null || fetchedContent.value !== null) return

    isFetchingContent.value = true
    fetchError.value = null
    try {
      const full = await api.getFilingItem(props.accession, item.item_number)
      fetchedContent.value = full.content_text
    } catch (e) {
      fetchError.value = e instanceof Error ? e.message : '內容載入失敗'
    } finally {
      isFetchingContent.value = false
    }
  },
)

// The text to render: prefer lazily fetched content, fall back to inline.
const activeContent = computed(() => fetchedContent.value ?? props.item?.content_text ?? null)

// Defer markdown render to a macrotask so the drawer animation isn't blocked
// by MarkdownIt + DOMPurify running synchronously on large content_text strings.
watch(
  activeContent,
  (text) => {
    if (!text) {
      renderedHtml.value = ''
      isRendering.value = false
      return
    }
    isRendering.value = true
    renderedHtml.value = ''
    setTimeout(() => {
      renderedHtml.value = renderMarkdown(text)
      isRendering.value = false
    }, 0)
  },
  { immediate: true },
)

const isLoading = computed(() => isFetchingContent.value || isRendering.value)
const charCount = computed(() => activeContent.value?.length ?? 0)
const hasContent = computed(
  () =>
    (props.item?.status === 'extracted' ||
      props.item?.status === 'incorporated_by_reference') &&
    (isLoading.value || !!renderedHtml.value),
)
const charRangeText = computed(() => {
  const r = props.item?.char_range
  return r ? `${r[0].toLocaleString()}–${r[1].toLocaleString()}` : null
})
</script>

<template>
  <Drawer :open="open" @close="emit('close')">
    <template #header>
      <div v-if="item" class="flex items-center gap-2 text-sm">
        <ItemStatusBadge :status="item.status" small />
        <span class="font-mono text-xs text-muted-foreground">Item {{ item.item_number }}</span>
        <span class="truncate font-semibold text-foreground">{{ item.item_title }}</span>
      </div>
    </template>

    <div v-if="item" class="px-5 py-4">
      <!-- Meta row -->
      <div class="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs text-muted-foreground">
        <span>{{ item.part }}</span>
        <span class="inline-flex items-center gap-1">
          狀態：<span class="text-foreground">{{ statusLabel(item.status) }}</span>
        </span>
        <span v-if="item.confidence != null">
          信心：<span class="tabular-nums text-foreground">{{ item.confidence.toFixed(2) }}</span>
        </span>
        <span v-if="charRangeText" class="font-mono">範圍 {{ charRangeText }}</span>
        <span v-if="charCount" class="tabular-nums">{{ charCount.toLocaleString() }} 字</span>
      </div>

      <!-- Item-level flags -->
      <ul v-if="flags.length" class="mt-4 space-y-1.5">
        <li
          v-for="(f, i) in flags"
          :key="i"
          class="flex items-start gap-2 rounded-md border border-border bg-muted/30 px-3 py-2"
        >
          <span
            class="mt-0.5 inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[11px] font-medium leading-none"
            :class="severityClasses(f.severity)"
          >
            {{ f.severity }}
          </span>
          <div class="min-w-0">
            <div class="text-sm font-medium text-foreground">{{ flagLabel(f.code) }}</div>
            <p class="mt-0.5 text-xs text-muted-foreground">{{ f.message }}</p>
          </div>
        </li>
      </ul>

      <hr class="my-4 border-border" />

      <!-- Content -->
      <div v-if="fetchError" class="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2.5 text-sm text-destructive">
        <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" />
        {{ fetchError }}
      </div>
      <div v-else-if="isLoading" class="space-y-3">
        <Skeleton class="h-4 w-full" />
        <Skeleton class="h-4 w-5/6" />
        <Skeleton class="h-4 w-full" />
        <Skeleton class="h-4 w-4/6" />
      </div>
      <div
        v-else-if="hasContent"
        class="markdown-body text-[15px] leading-[1.75] text-foreground"
        v-html="renderedHtml"
      />
      <div
        v-else-if="item.status === 'not_applicable'"
        class="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4"
      >
        <Minus class="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
        <p class="text-sm italic text-muted-foreground">公司聲明此項目不適用。</p>
      </div>
      <div
        v-else-if="item.status === 'reserved'"
        class="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4"
      >
        <Ban class="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
        <p class="text-sm text-muted-foreground">SEC 規定保留項目，此項目不預期有內容。</p>
      </div>
      <div
        v-else
        class="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4"
      >
        <ExternalLink class="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
        <p class="text-sm text-muted-foreground">
          此項目無可顯示內容（{{ statusLabel(item.status) }}）。
        </p>
      </div>
    </div>
  </Drawer>
</template>
