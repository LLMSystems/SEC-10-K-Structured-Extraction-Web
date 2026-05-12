<script setup lang="ts">
import { onMounted } from 'vue'
import { ArrowRight, Cpu, Send, Sparkles } from 'lucide-vue-next'
import ScanlineBackground from '@/components/common/ScanlineBackground.vue'
import ExtractionForm from '@/components/home/ExtractionForm.vue'
import { useJobStore } from '@/stores/job'

const jobStore = useJobStore()

onMounted(() => {
  if (jobStore.phase === 'error') jobStore.reset()
})

const steps = [
  { icon: Send, title: '送出請求', desc: '提供 CIK + Accession Number，或直接貼上 SEC EDGAR URL。' },
  { icon: Cpu, title: '非同步解析', desc: '從下載到結構化平均約 0.7 秒。' },
  {
    icon: ArrowRight,
    title: '結構化結果',
    desc: '依 Part 分組呈現每個 Item 的內文、狀態、字元範圍與處理時間。',
  },
]
</script>

<template>
  <div class="relative isolate min-h-[calc(100vh-3.5rem)] overflow-hidden">
    <ScanlineBackground />

    <div class="relative mx-auto flex max-w-screen-xl flex-col items-center px-4 pb-20 pt-16 sm:pt-24">
      <div class="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs text-muted-foreground backdrop-blur-md">
        <Sparkles class="h-3.5 w-3.5 text-primary" />
        <span>非同步解析 SEC 10-K · 重複查詢直接走快取</span>
      </div>

      <h1
        class="max-w-3xl text-center text-4xl font-semibold tracking-tight text-foreground sm:text-5xl"
      >
        SEC 10-K 財報
        <span class="text-primary">結構化抽取工具</span>
      </h1>
      <p class="mt-4 max-w-xl text-center text-base text-muted-foreground">
        通過文件識別碼，取得 Part I 到 Part IV 逐項拆解，包含內文、狀態。
      </p>

      <div class="mt-10 w-full max-w-xl">
        <ExtractionForm />
      </div>

      <section class="mt-24 w-full max-w-4xl">
        <div class="mb-6 flex items-center gap-3">
          <div class="h-px flex-1 bg-border" />
          <span class="text-[10px] font-semibold tracking-[0.2em] text-muted-foreground">
            運作方式
          </span>
          <div class="h-px flex-1 bg-border" />
        </div>

        <ol class="grid gap-4 sm:grid-cols-3">
          <li
            v-for="(step, i) in steps"
            :key="step.title"
            class="rounded-xl border border-border bg-card/50 p-5 backdrop-blur-sm"
          >
            <div class="flex items-center gap-2">
              <span
                class="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 text-primary ring-1 ring-primary/20"
              >
                <component :is="step.icon" class="h-3.5 w-3.5" />
              </span>
              <span class="font-mono text-[10px] text-muted-foreground">0{{ i + 1 }}</span>
            </div>
            <h3 class="mt-3 text-sm font-semibold text-foreground">{{ step.title }}</h3>
            <p class="mt-1 text-xs leading-relaxed text-muted-foreground">{{ step.desc }}</p>
          </li>
        </ol>
      </section>
    </div>
  </div>
</template>
