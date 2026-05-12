<script setup lang="ts">
import { storeToRefs } from 'pinia'
import Input from '@/components/ui/Input.vue'
import { useInputStore } from '@/stores/input'

const store = useInputStore()
const { cik, accessionNumber } = storeToRefs(store)
</script>

<template>
  <div class="grid gap-4 sm:grid-cols-2">
    <div class="space-y-1.5">
      <label
        for="cik"
        class="text-xs font-medium tracking-wider text-muted-foreground"
      >
        CIK
      </label>
      <Input
        id="cik"
        v-model="cik"
        mono
        placeholder="0000320193"
        autocomplete="off"
      />
    </div>
    <div class="space-y-1.5">
      <label
        for="accession"
        class="text-xs font-medium tracking-wider text-muted-foreground"
      >
        Accession Number
      </label>
      <Input
        id="accession"
        v-model="accessionNumber"
        mono
        placeholder="0000320193-23-000106"
        autocomplete="off"
      />
    </div>
  </div>
</template>
