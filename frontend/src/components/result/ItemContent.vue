<script setup lang="ts">
import { computed } from 'vue'
import { Ban, ExternalLink, FileText, Minus } from 'lucide-vue-next'
import Badge from '@/components/ui/Badge.vue'
import MonoText from '@/components/common/MonoText.vue'
import { renderMarkdown } from '@/lib/markdown'
import { statusLabel } from '@/lib/statusLabels'
import type { FilingItem } from '@/types/api'

const props = defineProps<{ item: FilingItem | null }>()

const charRangeText = computed(() => {
  if (!props.item?.char_range) return null
  const [a, b] = props.item.char_range
  return `字元範圍 ${a.toLocaleString()}–${b.toLocaleString()}`
})

const renderedHtml = computed(() => {
  if (!props.item?.content_text) return ''
  return renderMarkdown(props.item.content_text)
})
</script>

<template>
  <div v-if="!item" class="flex h-full flex-col items-center justify-center p-12 text-center">
    <FileText class="h-10 w-10 text-muted-foreground/60" />
    <p class="mt-4 text-sm font-medium text-foreground">請選擇一個項目</p>
    <p class="mt-1 text-xs text-muted-foreground">
      從左側導覽列點選任一項目以查看其內文。
    </p>
  </div>

  <article
    v-else
    :key="`${item.part}-${item.item_number}`"
    class="mx-auto max-w-3xl px-8 py-10 animate-in fade-in slide-in-from-right-1 duration-200"
  >
    <header class="mb-8">
      <div class="flex items-center gap-2 text-xs text-muted-foreground">
        <span class="font-medium tracking-widest">{{ item.part }}</span>
        <span aria-hidden>·</span>
        <span>Item {{ item.item_number }}</span>
        <Badge
          v-if="item.status === 'extracted'"
          variant="success"
          class="ml-auto"
        >
          已解析
        </Badge>
        <Badge
          v-else-if="item.status === 'incorporated_by_reference'"
          variant="info"
          class="ml-auto"
        >
          引用揭露
        </Badge>
        <Badge v-else variant="secondary" class="ml-auto">
          {{ statusLabel(item.status) }}
        </Badge>
      </div>
      <h1 class="mt-2 text-2xl font-semibold tracking-tight text-foreground">
        {{ item.item_title }}
      </h1>
      <MonoText v-if="charRangeText" class="mt-2 block text-xs text-muted-foreground">
        {{ charRangeText }}
      </MonoText>
    </header>

    <!-- Banner for incorporated_by_reference items (shown above content) -->
    <div
      v-if="item.status === 'incorporated_by_reference'"
      class="mb-6 flex items-start gap-3 rounded-lg border border-blue-500/30 bg-blue-500/5 p-4"
    >
      <ExternalLink class="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
      <div class="text-sm">
        <p class="font-medium text-foreground">以引用方式揭露</p>
        <p class="mt-1 text-muted-foreground">
          此項目的完整揭露位於另一份 SEC 文件（通常是 definitive proxy statement）。下方為 10-K
          中的引用通告原文。
        </p>
      </div>
    </div>

    <!-- Main content: extracted OR incorporated_by_reference (both can have content_text) -->
    <template
      v-if="
        (item.status === 'extracted' || item.status === 'incorporated_by_reference') &&
        renderedHtml
      "
    >
      <div
        class="markdown-body text-[15px] leading-[1.75] text-foreground"
        v-html="renderedHtml"
      />
    </template>

    <div
      v-else-if="item.status === 'not_applicable'"
      class="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4"
    >
      <Minus class="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      <p class="text-sm italic text-muted-foreground">
        公司聲明此項目不適用。
      </p>
    </div>

    <div
      v-else-if="item.status === 'reserved'"
      class="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4"
    >
      <Ban class="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
      <p class="text-sm text-muted-foreground">
        SEC 規定保留項目，此項目不預期有內容。
      </p>
    </div>
  </article>
</template>
