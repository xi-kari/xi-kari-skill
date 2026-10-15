<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { Content, useData, useRoute } from 'vitepress'
import XkTopBar from './components/XkTopBar.vue'
import XkBookNav from './components/XkBookNav.vue'
import XkAside from './components/XkAside.vue'
import XkTitleBlock from './components/XkTitleBlock.vue'
import XkPager from './components/XkPager.vue'
import XkFooter from './components/XkFooter.vue'
import XkNotFound from './components/XkNotFound.vue'
import XkSearch from './components/XkSearch.vue'
import XkLightbox from './components/XkLightbox.vue'
import { useReadingProgress } from './composables/outline'
import { startPrefs } from './composables/prefs'

/* the home page carries every lesson's title and lead, so it loads on its own */
const XkHome = defineAsyncComponent(() => import('./components/XkHome.vue'))

const { page, frontmatter } = useData()
const route = useRoute()

const isHome = computed(() => frontmatter.value.layout === 'home')
const isNotFound = computed(() => !!page.value.isNotFound)
const isTheory = computed(() => page.value.relativePath.startsWith('theory/'))

const navOpen = ref(false)
const asideOpen = ref(false)
const searchOpen = ref(false)
const progress = useReadingProgress()
const drawerOpen = computed(() => navOpen.value || asideOpen.value)
let returnFocus: HTMLElement | null = null
let restoreFocus = true
let focusFrame = 0
const focusSelector = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

function closeDrawers(restore = true) {
  restoreFocus = restore
  navOpen.value = false
  asideOpen.value = false
}
function rememberTrigger() {
  if (!drawerOpen.value) returnFocus = document.activeElement as HTMLElement | null
  restoreFocus = true
}
function toggleNav() {
  rememberTrigger()
  asideOpen.value = false
  navOpen.value = !navOpen.value
}
function toggleAside() {
  rememberTrigger()
  navOpen.value = false
  asideOpen.value = !asideOpen.value
}
function activeDrawer(): HTMLElement | null {
  if (!drawerOpen.value) return null
  return document.querySelector(navOpen.value ? '#xk-nav' : '#xk-aside')
}
function focusableItems(panel: HTMLElement) {
  return [...panel.querySelectorAll<HTMLElement>(focusSelector)]
    .filter((element) => element.getClientRects().length && !element.closest('[inert]') && getComputedStyle(element).visibility !== 'hidden')
}
function focusDrawer() {
  const panel = activeDrawer()
  if (panel) (focusableItems(panel)[0] || panel).focus({ preventScroll: true })
}
function onKey(event: KeyboardEvent) {
  if (!drawerOpen.value) return
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    closeDrawers()
  } else if (event.key === 'Tab') {
    const panel = activeDrawer()
    if (!panel) return
    const items = focusableItems(panel)
    const first = items[0]
    const last = items[items.length - 1]
    if (!first) {
      event.preventDefault()
      panel.focus()
    } else if (!panel.contains(document.activeElement) || (event.shiftKey && document.activeElement === first) || (!event.shiftKey && document.activeElement === last)) {
      event.preventDefault()
      ;(event.shiftKey ? last : first).focus()
    }
  }
}
function containFocus(event: FocusEvent) {
  const panel = activeDrawer()
  if (panel && !searchOpen.value && !panel.contains(event.target as Node)) focusDrawer()
}
function onResize() {
  if ((navOpen.value && window.innerWidth >= 1024) || (asideOpen.value && window.innerWidth >= 1280)) closeDrawers()
}

watch(() => route.path, () => {
  closeDrawers(false)
  nextTick(() => document.querySelector<HTMLElement>('#xk-main')?.focus({ preventScroll: true }))
})
watch(searchOpen, (open) => { if (open && drawerOpen.value) closeDrawers(false) })
watch([navOpen, asideOpen], async ([nav, aside], [wasNav, wasAside]) => {
  document.documentElement.classList.toggle('xk-locked', nav || aside)
  cancelAnimationFrame(focusFrame)
  if (nav || aside) {
    await nextTick()
    focusFrame = requestAnimationFrame(focusDrawer)
  } else if (wasNav || wasAside) {
    const target = returnFocus
    returnFocus = null
    if (!restoreFocus) return
    await nextTick()
    if (target?.isConnected && target.getClientRects().length) target.focus({ preventScroll: true })
    else document.querySelector<HTMLElement>('#xk-main')?.focus({ preventScroll: true })
  }
}, { flush: 'post' })

onMounted(() => {
  startPrefs()
  window.addEventListener('keydown', onKey, true)
  document.addEventListener('focusin', containFocus)
  window.addEventListener('resize', onResize, { passive: true })
})
onUnmounted(() => {
  cancelAnimationFrame(focusFrame)
  document.documentElement.classList.remove('xk-locked')
  window.removeEventListener('keydown', onKey, true)
  document.removeEventListener('focusin', containFocus)
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <div class="xk-app" :class="{ 'is-home': isHome, 'nav-open': navOpen, 'aside-open': asideOpen }">
    <a class="xk-skip" href="#xk-main" :inert="drawerOpen || undefined">跳到正文</a>
    <XkTopBar
      :inert="drawerOpen || undefined"
      :progress="progress"
      :nav-open="navOpen"
      :aside-open="asideOpen"
      :has-nav="!isNotFound"
      :has-aside="!isHome && !isNotFound"
      @toggle-nav="toggleNav"
      @toggle-aside="toggleAside"
      @search="searchOpen = true"
    />

    <XkNotFound v-if="isNotFound" :inert="drawerOpen || undefined" />

    <template v-else-if="isHome">
      <main id="xk-main" tabindex="-1" :inert="drawerOpen || undefined"><XkHome /></main>
      <XkBookNav class="xk-nav--drawer" :open="navOpen" :role="navOpen ? 'dialog' : undefined" :aria-modal="navOpen || undefined" :tabindex="navOpen ? -1 : undefined" @close="closeDrawers()" />
    </template>

    <div v-else class="xk-desk">
      <XkBookNav :open="navOpen" :inert="asideOpen || undefined" :role="navOpen ? 'dialog' : undefined" :aria-modal="navOpen || undefined" :tabindex="navOpen ? -1 : undefined" @close="closeDrawers()" />
      <main id="xk-main" class="xk-sheet" tabindex="-1" :inert="drawerOpen || undefined">
        <div class="xk-sheet__inner">
          <XkTitleBlock v-if="isTheory" />
          <Content class="xk-prose" :class="{ 'is-theory': isTheory }" />
          <XkPager />
        </div>
      </main>
      <XkAside :open="asideOpen" :is-theory="isTheory" :inert="navOpen || undefined" :role="asideOpen ? 'dialog' : undefined" :aria-modal="asideOpen || undefined" :tabindex="asideOpen ? -1 : undefined" @close="closeDrawers()" />
    </div>

    <XkFooter :inert="drawerOpen || undefined" />
    <div v-if="drawerOpen" class="xk-scrim" aria-hidden="true" @click="closeDrawers()" />
    <XkSearch v-model:open="searchOpen" />
    <XkLightbox />
  </div>
</template>
