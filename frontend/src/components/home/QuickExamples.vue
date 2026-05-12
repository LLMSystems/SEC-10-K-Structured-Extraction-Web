<script setup lang="ts">
import { Sparkles } from 'lucide-vue-next'
import { EXAMPLES, useInputStore } from '@/stores/input'

const store = useInputStore()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <span class="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <Sparkles class="h-3.5 w-3.5" />
      範例：
    </span>
    <button
      v-for="ex in EXAMPLES"
      :key="ex.label"
      type="button"
      @click="store.fillExample(ex)"
      class="rounded-full border border-border bg-background px-3 py-1 text-xs text-foreground transition-all hover:border-primary/40 hover:bg-primary/5 hover:text-primary active:scale-[0.97]"
    >
      {{ ex.label }}
    </button>
  </div>
</template>
