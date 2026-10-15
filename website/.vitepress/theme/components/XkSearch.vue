<script setup lang="ts">
import { defineAsyncComponent, onMounted, onUnmounted } from 'vue'

const open = defineModel<boolean>('open', { default: false })
const SearchBox = defineAsyncComponent(() => import('vitepress/dist/client/theme-default/components/VPLocalSearchBox.vue'))

function editing(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null
  if (!el) return false
  return el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName)
}

function onKey(event: KeyboardEvent) {
  if ((event.key === 'k' || event.key === 'K') && (event.metaKey || event.ctrlKey)) {
    event.preventDefault()
    open.value = !open.value
  } else if (event.key === '/' && !open.value && !editing(event.target)) {
    event.preventDefault()
    open.value = true
  }
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <SearchBox v-if="open" @close="open = false" />
</template>
