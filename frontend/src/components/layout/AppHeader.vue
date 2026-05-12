<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, FileText, Moon, Sun } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { useThemeStore } from '@/stores/theme'
import { useJobStore } from '@/stores/job'

const route = useRoute()
const router = useRouter()
const themeStore = useThemeStore()
const jobStore = useJobStore()

const isResult = computed(() => route.name === 'result')
const companyName = computed(
  () => jobStore.filingResult?.filing_info.company_name ?? null,
)
const fiscalYear = computed(() => {
  const fye = jobStore.filingResult?.filing_info.fiscal_year_end
  if (!fye) return null
  const year = fye.slice(0, 4)
  return `FY${year}`
})

function goHome() {
  router.push('/')
}
</script>

<template>
  <header
    class="sticky top-0 z-40 h-14 w-full border-b border-border bg-background/80 backdrop-blur-md"
  >
    <div class="mx-auto flex h-full max-w-screen-2xl items-center gap-3 px-4">
      <button
        v-if="isResult"
        class="-ml-1 flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        @click="goHome"
        aria-label="返回首頁"
      >
        <ArrowLeft class="h-4 w-4" />
      </button>

      <RouterLink to="/" class="flex items-center gap-2 group">
        <span
          class="flex h-7 w-7 items-center justify-center rounded-md bg-primary/10 text-primary ring-1 ring-primary/20 transition-all group-hover:ring-primary/40"
        >
          <FileText class="h-4 w-4" />
        </span>
        <span class="font-semibold tracking-tight text-foreground">
          SEC 10-K 解析器
        </span>
      </RouterLink>

      <template v-if="isResult && companyName">
        <span class="mx-2 h-4 w-px bg-border" aria-hidden />
        <span class="flex items-baseline gap-2 text-sm">
          <span class="font-medium text-foreground">{{ companyName }}</span>
          <span v-if="fiscalYear" class="font-mono text-xs text-muted-foreground">
            · {{ fiscalYear }}
          </span>
        </span>
      </template>

      <div class="ml-auto flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          @click="themeStore.toggle()"
          :aria-label="`切換為${themeStore.theme === 'dark' ? '淺色' : '深色'}模式`"
        >
          <Sun v-if="themeStore.theme === 'dark'" class="h-4 w-4" />
          <Moon v-else class="h-4 w-4" />
        </Button>
        <a
          href="https://github.com/"
          target="_blank"
          rel="noopener"
          class="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          aria-label="GitHub 原始碼"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            class="h-4 w-4"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              d="M12 .5C5.65.5.5 5.65.5 12c0 5.09 3.29 9.4 7.86 10.93.58.1.79-.25.79-.56v-2c-3.19.69-3.86-1.36-3.86-1.36-.52-1.32-1.28-1.67-1.28-1.67-1.05-.72.08-.71.08-.71 1.16.08 1.78 1.2 1.78 1.2 1.03 1.76 2.7 1.25 3.36.95.1-.75.4-1.25.73-1.54-2.55-.29-5.23-1.28-5.23-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.47.11-3.06 0 0 .97-.31 3.18 1.18.92-.26 1.91-.39 2.89-.39.98 0 1.97.13 2.89.39 2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.77.11 3.06.74.81 1.19 1.84 1.19 3.1 0 4.42-2.69 5.39-5.25 5.68.41.36.78 1.06.78 2.13v3.16c0 .31.21.67.8.56C20.21 21.4 23.5 17.09 23.5 12 23.5 5.65 18.35.5 12 .5z"
            />
          </svg>
        </a>
      </div>
    </div>
  </header>
</template>
