<script setup lang="ts">
import { computed } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import ItemStatusBadge from './ItemStatusBadge.vue'
import { useNavigatorStore } from '@/stores/navigator'
import type { FilingItem } from '@/types/api'

const props = defineProps<{ items: FilingItem[] }>()

const navigator = useNavigatorStore()

const visibleItems = computed(() =>
  props.items
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => item.status !== 'missing'),
)

const grouped = computed(() => {
  const map = new Map<string, { item: FilingItem; index: number }[]>()
  for (const row of visibleItems.value) {
    const part = row.item.part || 'Other'
    if (!map.has(part)) map.set(part, [])
    map.get(part)!.push(row)
  }
  return Array.from(map.entries())
})

function selectable(status: FilingItem['status']) {
  return status !== 'reserved'
}
</script>

<template>
  <nav class="flex h-full flex-col">
    <div
      class="sticky top-0 z-10 flex items-baseline justify-between border-b border-border bg-card px-4 py-3"
    >
      <span class="text-[10px] font-semibold tracking-widest text-muted-foreground">
        項目清單
      </span>
      <span class="font-mono text-xs text-muted-foreground">
        {{ visibleItems.length }}
      </span>
    </div>

    <div class="flex-1 overflow-y-auto px-2 py-2">
      <div v-for="[part, rows] in grouped" :key="part" class="mb-3">
        <button
          type="button"
          class="flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-semibold tracking-widest text-muted-foreground transition-colors hover:text-foreground"
          @click="navigator.togglePart(part)"
        >
          <ChevronDown
            :class="[
              'h-3 w-3 transition-transform',
              navigator.isPartExpanded(part) ? '' : '-rotate-90',
            ]"
          />
          {{ part }}
        </button>

        <ul v-show="navigator.isPartExpanded(part)" class="mt-1 space-y-0.5">
          <li v-for="{ item, index } in rows" :key="index">
            <button
              type="button"
              :disabled="!selectable(item.status)"
              :class="[
                'group flex w-full items-center gap-2 rounded-md py-1.5 pl-3 pr-2 text-left text-sm transition-colors',
                navigator.activeItemIndex === index
                  ? 'bg-primary/10 text-primary'
                  : selectable(item.status)
                    ? 'text-foreground hover:bg-accent'
                    : 'cursor-default text-muted-foreground',
              ]"
              @click="selectable(item.status) && navigator.setActiveItem(index)"
            >
              <span class="font-mono text-[11px] text-muted-foreground">
                {{ item.item_number }}
              </span>
              <span class="flex-1 truncate text-[13px]">{{ item.item_title }}</span>
              <ItemStatusBadge :status="item.status" />
            </button>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
