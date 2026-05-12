<script setup lang="ts">
import { storeToRefs } from 'pinia'
import Input from '@/components/ui/Input.vue'
import { useInputStore } from '@/stores/input'

const store = useInputStore()
const { url } = storeToRefs(store)
</script>

<template>
  <div class="space-y-1.5">
    <label
      for="url"
      class="text-xs font-medium tracking-wider text-muted-foreground"
    >
      SEC EDGAR URL
    </label>
    <Input
      id="url"
      v-model="url"
      mono
      placeholder="https://www.sec.gov/Archives/edgar/data/320193/..."
      autocomplete="off"
    />
    <p class="text-xs text-muted-foreground">
      貼上主文件 URL，系統會自動解析出 CIK 與 Accession Number。
    </p>
  </div>
</template>
