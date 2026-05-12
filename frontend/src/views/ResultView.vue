<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertCircle, ArrowLeft, Download } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import FilingInfoCard from '@/components/result/FilingInfoCard.vue'
import ItemNavigator from '@/components/result/ItemNavigator.vue'
import ItemContent from '@/components/result/ItemContent.vue'
import ShareButton from '@/components/result/ShareButton.vue'
import { useJobStore } from '@/stores/job'
import { useNavigatorStore } from '@/stores/navigator'

const route = useRoute()
const router = useRouter()
const jobStore = useJobStore()
const navigator = useNavigatorStore()

const jobId = computed(() => route.params.jobId as string)

const activeItem = computed(() => {
  if (!jobStore.filingResult || navigator.activeItemIndex === null) return null
  return jobStore.filingResult.items[navigator.activeItemIndex] ?? null
})

async function ensureLoaded() {
  // Already loaded with same job id? skip.
  if (jobStore.jobId === jobId.value && jobStore.filingResult) {
    pickFirstExtracted()
    return
  }
  await jobStore.loadJobById(jobId.value)
  pickFirstExtracted()
}

function pickFirstExtracted() {
  if (!jobStore.filingResult) return
  navigator.reset()
  const firstIdx = jobStore.filingResult.items.findIndex((i) => i.status === 'extracted')
  navigator.setActiveItem(firstIdx >= 0 ? firstIdx : 0)
}

onMounted(ensureLoaded)
watch(jobId, ensureLoaded)

function downloadJson() {
  if (!jobStore.filingResult) return
  const blob = new Blob([JSON.stringify(jobStore.filingResult, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${jobStore.filingResult.filing_info.accession_number}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const isLoading = computed(
  () => !jobStore.filingResult && (jobStore.isLoading || jobStore.phase === 'idle'),
)
const isError = computed(() => jobStore.phase === 'error' && !jobStore.filingResult)
</script>

<template>
  <!-- Error state -->
  <div
    v-if="isError"
    class="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center"
  >
    <div
      class="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-destructive/30 bg-destructive/10"
    >
      <AlertCircle class="h-5 w-5 text-destructive" />
    </div>
    <h1 class="text-lg font-semibold text-foreground">無法載入此結果</h1>
    <p class="mt-1 text-sm text-muted-foreground">{{ jobStore.error }}</p>
    <Button variant="outline" class="mt-6" @click="router.push('/')">
      <ArrowLeft class="h-4 w-4" />
      返回首頁
    </Button>
  </div>

  <!-- Loading state -->
  <div
    v-else-if="isLoading"
    class="mx-auto grid h-[calc(100vh-3.5rem)] max-w-screen-2xl grid-cols-[16rem_14rem_1fr] gap-4 px-4 py-6"
  >
    <Skeleton class="h-full" />
    <Skeleton class="h-full" />
    <div class="space-y-4">
      <Skeleton class="h-8 w-1/3" />
      <Skeleton class="h-4 w-1/2" />
      <Skeleton class="h-32 w-full" />
      <Skeleton class="h-32 w-full" />
    </div>
  </div>

  <!-- Loaded state -->
  <div
    v-else-if="jobStore.filingResult"
    class="mx-auto max-w-screen-2xl px-4 py-4 animate-in fade-in duration-300"
  >
    <!-- Sub-header / actions -->
    <div class="mb-3 flex items-center justify-between">
      <p class="text-xs text-muted-foreground">
        共擷取 {{ jobStore.filingResult.items.length }} 個項目
      </p>
      <div class="flex items-center gap-2">
        <ShareButton />
        <Button variant="outline" size="sm" @click="downloadJson">
          <Download class="h-3.5 w-3.5" />
          下載 JSON
        </Button>
      </div>
    </div>

    <div class="grid h-[calc(100vh-7.5rem)] gap-4 lg:grid-cols-[16rem_15rem_1fr]">
      <!-- Left: filing info -->
      <aside class="hidden overflow-y-auto lg:block">
        <FilingInfoCard :filing="jobStore.filingResult" />
      </aside>

      <!-- Middle: item navigator -->
      <aside
        class="overflow-hidden rounded-xl border border-border bg-card shadow-sm lg:col-span-1"
      >
        <ItemNavigator :items="jobStore.filingResult.items" />
      </aside>

      <!-- Right: content -->
      <main class="overflow-y-auto rounded-xl border border-border bg-card shadow-sm">
        <ItemContent :item="activeItem" />
      </main>
    </div>
  </div>
</template>
