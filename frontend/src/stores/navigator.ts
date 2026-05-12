import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNavigatorStore = defineStore('navigator', () => {
  const activeItemIndex = ref<number | null>(null)
  const expandedParts = ref<Set<string>>(new Set(['Part I', 'Part II', 'Part III', 'Part IV']))

  function setActiveItem(index: number) {
    activeItemIndex.value = index
  }

  function togglePart(part: string) {
    const next = new Set(expandedParts.value)
    if (next.has(part)) next.delete(part)
    else next.add(part)
    expandedParts.value = next
  }

  function isPartExpanded(part: string): boolean {
    return expandedParts.value.has(part)
  }

  function reset() {
    activeItemIndex.value = null
    expandedParts.value = new Set(['Part I', 'Part II', 'Part III', 'Part IV'])
  }

  return { activeItemIndex, expandedParts, setActiveItem, togglePart, isPartExpanded, reset }
})
