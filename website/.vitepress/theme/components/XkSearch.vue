<script setup lang="ts">
import { defineAsyncComponent, nextTick, onMounted, onUnmounted, watch } from 'vue'

const open = defineModel<boolean>('open', { default: false })
const SearchBox = defineAsyncComponent(() => import('vitepress/dist/client/theme-default/components/VPLocalSearchBox.vue'))
let trigger: HTMLElement | null = null
let openedAt = ''
let focusFrame = 0

// The search box is teleported and unmounted on close. Restore keyboard position
// after its focus trap releases; a drawer trigger may already have been hidden.
watch(open, async (shown) => {
  cancelAnimationFrame(focusFrame)
  if (shown) {
    trigger = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const drawerClose = trigger?.closest('#xk-nav, #xk-aside')?.querySelector<HTMLElement>('.xk-drawer-close')
    if (drawerClose && getComputedStyle(drawerClose).display !== 'none') {
      trigger = document.querySelector<HTMLElement>('.xk-search-btn')
    }
    openedAt = location.href
    return
  }
  const target = trigger
  trigger = null
  await nextTick()
  focusFrame = requestAnimationFrame(() => {
    if (open.value || location.href !== openedAt) return
    const available = (element: HTMLElement | null): element is HTMLElement => !!element &&
      element !== document.body && element.isConnected && !!element.getClientRects().length &&
      !element.closest('[inert]') && getComputedStyle(element).visibility !== 'hidden'
    const fallback = document.querySelector<HTMLElement>('.xk-search-btn')
    if (available(target)) target.focus({ preventScroll: true })
    else if (available(fallback)) fallback.focus({ preventScroll: true })
  })
}, { flush: 'sync' })

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
onUnmounted(() => {
  cancelAnimationFrame(focusFrame)
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <SearchBox v-if="open" @close="open = false" />
</template>
