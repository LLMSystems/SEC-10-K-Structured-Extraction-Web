import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api, ApiError } from '@/lib/api'
import type {
  FilingOutput,
  JobResponse,
  JobSubmitInput,
} from '@/types/api'

export type JobPhase = 'idle' | 'submitting' | 'polling' | 'cache_hit' | 'done' | 'error'

const MAX_POLLS = 60 // 60 seconds max

export const useJobStore = defineStore('job', () => {
  const phase = ref<JobPhase>('idle')
  const jobId = ref<string | null>(null)
  const cacheHit = ref(false)
  const currentJob = ref<JobResponse | null>(null)
  const filingResult = ref<FilingOutput | null>(null)
  const error = ref<string | null>(null)

  let pollTimer: ReturnType<typeof setInterval> | null = null
  let pollCount = 0

  const isLoading = computed(() => phase.value === 'submitting' || phase.value === 'polling')

  function stopPolling() {
    if (pollTimer !== null) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    pollCount = 0
  }

  function reset() {
    stopPolling()
    phase.value = 'idle'
    jobId.value = null
    cacheHit.value = false
    currentJob.value = null
    filingResult.value = null
    error.value = null
  }

  async function fetchFinal(id: string) {
    const job = await api.getJob(id)
    currentJob.value = job
    if (job.status === 'done' && job.result) {
      filingResult.value = job.result
      phase.value = 'done'
    } else if (job.status === 'failed') {
      error.value = job.error ?? 'Job 執行失敗'
      phase.value = 'error'
    }
  }

  function startPolling(id: string) {
    stopPolling()
    phase.value = 'polling'
    pollCount = 0
    pollTimer = setInterval(async () => {
      pollCount++
      if (pollCount > MAX_POLLS) {
        error.value = '處理時間超過預期，請稍後再試。'
        phase.value = 'error'
        stopPolling()
        return
      }
      try {
        const job = await api.getJob(id)
        currentJob.value = job
        if (job.status === 'done' && job.result) {
          filingResult.value = job.result
          phase.value = 'done'
          stopPolling()
        } else if (job.status === 'failed') {
          error.value = job.error ?? 'Job 執行失敗'
          phase.value = 'error'
          stopPolling()
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : '查詢狀態時發生未知錯誤'
        error.value = message
        phase.value = 'error'
        stopPolling()
      }
    }, 1000)
  }

  async function submitJob(input: JobSubmitInput) {
    reset()
    phase.value = 'submitting'
    try {
      const resp = await api.submitJob(input)
      jobId.value = resp.job_id
      cacheHit.value = resp.cache_hit

      if (resp.cache_hit || resp.status === 'done') {
        // Fetch result immediately
        phase.value = 'cache_hit'
        await fetchFinal(resp.job_id)
      } else {
        startPolling(resp.job_id)
      }
    } catch (err) {
      if (err instanceof ApiError) {
        error.value = err.message
      } else {
        error.value = err instanceof Error ? err.message : '送出請求失敗'
      }
      phase.value = 'error'
    }
  }

  async function loadJobById(id: string) {
    reset()
    jobId.value = id
    phase.value = 'polling'
    try {
      const job = await api.getJob(id)
      currentJob.value = job
      if (job.status === 'done' && job.result) {
        filingResult.value = job.result
        phase.value = 'done'
      } else if (job.status === 'failed') {
        error.value = job.error ?? 'Job 執行失敗'
        phase.value = 'error'
      } else {
        // pending/running: keep polling
        startPolling(id)
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        error.value = '找不到此 Job。'
      } else {
        error.value = err instanceof Error ? err.message : '載入 Job 失敗'
      }
      phase.value = 'error'
    }
  }

  return {
    phase,
    jobId,
    cacheHit,
    currentJob,
    filingResult,
    error,
    isLoading,
    submitJob,
    loadJobById,
    stopPolling,
    reset,
  }
})
