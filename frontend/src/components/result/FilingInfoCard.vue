<script setup lang="ts">
import { computed } from 'vue'
import { Building2 } from 'lucide-vue-next'
import Card from '@/components/ui/Card.vue'
import Separator from '@/components/ui/Separator.vue'
import MonoText from '@/components/common/MonoText.vue'
import TimingChart from './TimingChart.vue'
import { statusLabel } from '@/lib/statusLabels'
import type { FilingOutput } from '@/types/api'

const props = defineProps<{ filing: FilingOutput }>()

const info = computed(() => props.filing.filing_info)

const fiscalYearDisplay = computed(() => {
  if (!info.value.fiscal_year_end) return null
  return info.value.fiscal_year_end
})

const itemCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const item of props.filing.items) {
    counts[item.status] = (counts[item.status] ?? 0) + 1
  }
  return counts
})
</script>

<template>
  <Card class="overflow-hidden">
    <div class="space-y-1 border-b border-border bg-muted/30 p-4">
      <div class="flex items-center gap-2 text-muted-foreground">
        <Building2 class="h-3.5 w-3.5" />
        <span class="text-[10px] font-semibold tracking-widest">公司資訊</span>
      </div>
      <h2 class="text-lg font-semibold leading-tight text-foreground">
        {{ info.company_name ?? '未知申報人' }}
      </h2>
    </div>

    <div class="space-y-3 p-4 text-sm">
      <div class="flex items-baseline justify-between gap-2">
        <span class="text-xs text-muted-foreground">CIK</span>
        <MonoText class="text-foreground">{{ info.cik }}</MonoText>
      </div>
      <div class="flex items-baseline justify-between gap-2">
        <span class="text-xs text-muted-foreground">Accession</span>
        <MonoText class="text-foreground text-[11px]">
          {{ info.accession_number }}
        </MonoText>
      </div>
      <div v-if="fiscalYearDisplay" class="flex items-baseline justify-between gap-2">
        <span class="text-xs text-muted-foreground">會計年度結束</span>
        <MonoText class="text-foreground">{{ fiscalYearDisplay }}</MonoText>
      </div>
      <div v-if="info.filer_category" class="flex items-baseline justify-between gap-2">
        <span class="text-xs text-muted-foreground">申報人類別</span>
        <span class="text-right text-xs text-foreground">{{ info.filer_category }}</span>
      </div>
    </div>

    <Separator />

    <div class="space-y-2 p-4 text-xs">
      <span class="text-[10px] font-semibold tracking-widest text-muted-foreground">
        項目統計
      </span>
      <div class="grid grid-cols-2 gap-1.5">
        <div
          v-for="(count, status) in itemCounts"
          :key="status"
          class="flex items-baseline justify-between rounded-md bg-muted/40 px-2 py-1"
        >
          <span class="truncate text-[10px] text-muted-foreground">
            {{ statusLabel(status) }}
          </span>
          <span class="font-mono font-medium text-foreground">{{ count }}</span>
        </div>
      </div>
    </div>

    <Separator />

    <div class="p-4">
      <TimingChart :timing="props.filing.timing" />
    </div>
  </Card>
</template>
