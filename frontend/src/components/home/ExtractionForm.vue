<script setup lang="ts">
import { computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ArrowRight } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Tabs from '@/components/ui/Tabs.vue'
import TabsList from '@/components/ui/TabsList.vue'
import TabsTrigger from '@/components/ui/TabsTrigger.vue'
import TabsContent from '@/components/ui/TabsContent.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import CikInputGroup from './CikInputGroup.vue'
import UrlInputGroup from './UrlInputGroup.vue'
import QuickExamples from './QuickExamples.vue'
import JobProgressBar from './JobProgressBar.vue'

import { useInputStore } from '@/stores/input'
import { useJobStore } from '@/stores/job'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const inputStore = useInputStore()
const jobStore = useJobStore()
const toastStore = useToastStore()

const { mode, validation } = storeToRefs(inputStore)

const showProgress = computed(() =>
  ['submitting', 'polling', 'cache_hit', 'error'].includes(jobStore.phase),
)

const submitDisabled = computed(() => !validation.value.ok || jobStore.isLoading)

async function onSubmit(e: Event) {
  e.preventDefault()
  if (!validation.value.ok || !validation.value.payload) return
  await jobStore.submitJob(validation.value.payload)
}

// Navigate to result when ready; toast on cache hit.
// flush: 'post' 確保 watcher 在 Vue 完成所有組件更新後才執行，
// 避免在 setInterval async 回調觸發 phase='done' 時，Vue 更新佇列
// 尚未刷完就呼叫 router.push 造成間歇性靜默失敗。
watch(
  () => jobStore.phase,
  (phase, prev) => {
    if (phase === 'done' && jobStore.jobId) {
      // 立即 capture 當下的 jobId，避免 nextTick/setTimeout 執行時
      // store 被 reset 而讀到 null
      const targetId = jobStore.jobId
      if (jobStore.cacheHit) {
        toastStore.push({
          title: '快取命中',
          description: '此文件先前已處理過，直接載入快取結果。',
          variant: 'info',
          duration: 2500,
        })
        nextTick(() => router.push(`/result/${targetId}`))
      } else {
        nextTick(() => router.push(`/result/${targetId}`))
      }
    }
    if (phase === 'error' && prev !== 'error') {
      toastStore.push({
        title: '解析失敗',
        description: jobStore.error ?? '未知錯誤',
        variant: 'error',
        duration: 4500,
      })
    }
  },
  { flush: 'post' },
)

function setMode(v: string) {
  inputStore.setMode(v as 'cik' | 'url')
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <Card class="overflow-hidden border-border/80 backdrop-blur-sm">
      <div class="h-px w-full bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
      <CardContent class="p-6">
        <form @submit="onSubmit" class="space-y-5">
          <Tabs :model-value="mode" @update:model-value="setMode">
            <TabsList class="w-full">
              <TabsTrigger value="cik" class="flex-1">CIK + Accession Number</TabsTrigger>
              <TabsTrigger value="url" class="flex-1">SEC URL</TabsTrigger>
            </TabsList>

            <TabsContent value="cik">
              <CikInputGroup />
            </TabsContent>
            <TabsContent value="url">
              <UrlInputGroup />
            </TabsContent>
          </Tabs>

          <p
            v-if="validation.message && !jobStore.isLoading"
            class="text-xs text-muted-foreground"
          >
            {{ validation.message }}
          </p>

          <Button
            type="submit"
            size="lg"
            class="w-full"
            :disabled="submitDisabled"
          >
            <LoadingSpinner v-if="jobStore.isLoading" />
            <template v-else>
              開始解析
              <ArrowRight class="h-4 w-4" />
            </template>
          </Button>
        </form>
      </CardContent>
    </Card>

    <div class="px-1">
      <QuickExamples />
    </div>

    <JobProgressBar v-if="showProgress" :job-id="jobStore.jobId" />
  </div>
</template>
