<script setup lang="ts"></script>

<template>
  <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
    <div class="absolute inset-x-0 top-0 h-[480px] scanlines opacity-60" />
    <div class="absolute inset-x-0 top-0 h-[420px] grid-fade opacity-50" />
    <div
      class="absolute left-1/2 top-0 h-[320px] w-[680px] -translate-x-1/2 rounded-full bg-primary/5 blur-3xl"
    />
  </div>
</template>
