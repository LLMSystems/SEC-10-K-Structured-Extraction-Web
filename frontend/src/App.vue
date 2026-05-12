<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppToast from '@/components/layout/AppToast.vue'
import { useThemeStore } from '@/stores/theme'

// Initialize theme store (applies class to <html>)
useThemeStore()
</script>

<template>
  <div class="min-h-screen bg-background text-foreground">
    <AppHeader />
    <RouterView v-slot="{ Component }">
      <transition
        enter-active-class="transition-opacity duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
      >
        <component :is="Component" />
      </transition>
    </RouterView>
    <AppToast />
  </div>
</template>
