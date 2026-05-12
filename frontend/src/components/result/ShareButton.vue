<script setup lang="ts">
import { ref } from 'vue'
import { Check, Link2 } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { useToastStore } from '@/stores/toast'

const copied = ref(false)
const toastStore = useToastStore()

async function copyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    copied.value = true
    toastStore.push({
      title: '已複製連結',
      description: '任何人開啟此網址即可直接載入此結果。',
      variant: 'success',
      duration: 2500,
    })
    setTimeout(() => (copied.value = false), 1800)
  } catch {
    toastStore.push({
      title: '複製失敗',
      description: '無法存取剪貼簿。',
      variant: 'error',
    })
  }
}
</script>

<template>
  <Button variant="outline" size="sm" @click="copyLink">
    <Check v-if="copied" class="h-3.5 w-3.5 text-emerald-500" />
    <Link2 v-else class="h-3.5 w-3.5" />
    {{ copied ? '已複製' : '分享連結' }}
  </Button>
</template>
