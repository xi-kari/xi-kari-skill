<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { onContentUpdated } from 'vitepress'
import { canTransition } from '../composables/transitions'

type TransitionDocument = Document & { startViewTransition?: (update: () => Promise<void> | void) => { finished: Promise<void> } }

const dialog = ref<HTMLDialogElement>()
const src = ref('')
const alt = ref('')
const caption = ref('')
const originalSize = ref(false)
let source: HTMLImageElement | null = null
const ZOOMABLE = '.xk-plate img, .xk-prose .concept-figure img'

function swap(update: () => void, from: HTMLElement | null, to: () => HTMLElement | null) {
  const doc = document as TransitionDocument
  if (!canTransition() || !doc.startViewTransition || !from) {
    update()
    return
  }
  from.style.viewTransitionName = 'xk-zoom'
  doc.startViewTransition(async () => {
    from.style.viewTransitionName = ''
    update()
    await nextTick()
    const target = to()
    if (target) target.style.viewTransitionName = 'xk-zoom'
  }).finished.finally(() => {
    const target = to()
    if (target) target.style.viewTransitionName = ''
  })
}

function show(img: HTMLImageElement) {
  originalSize.value = false
  source = img
  src.value = img.currentSrc || img.src
  alt.value = img.alt
  caption.value = img.closest('figure')?.querySelector('figcaption')?.textContent?.trim() || ''
  swap(() => dialog.value?.showModal(), img, () => dialog.value?.querySelector('img') ?? null)
}

function hide() {
  if (!dialog.value?.open) return
  const back = source
  swap(() => dialog.value?.close(), dialog.value.querySelector('img'), () => back)
  back?.closest<HTMLElement>('button, [tabindex]')?.focus({ preventScroll: true })
}

function onClick(event: MouseEvent) {
  const img = (event.target as HTMLElement | null)?.closest<HTMLElement>('.xk-plate__zoom, ' + ZOOMABLE)
  if (!img || img.closest('a')) return
  const target = img.tagName === 'IMG' ? (img as HTMLImageElement) : img.querySelector('img')
  if (!target) return
  event.preventDefault()
  show(target)
}

function onKey(event: KeyboardEvent) {
  const el = event.target as HTMLElement
  if ((event.key === 'Enter' || event.key === ' ') && el.matches?.(ZOOMABLE)) {
    event.preventDefault()
    show(el as HTMLImageElement)
  }
}

function enhance() {
  document.querySelectorAll<HTMLImageElement>('.xk-prose .concept-figure img').forEach((img) => {
    img.tabIndex = 0
    img.setAttribute('role', 'button')
    img.setAttribute('aria-label', `放大图示：${img.alt || '图示'}`)
  })
}

onContentUpdated(enhance)
onMounted(() => {
  enhance()
  document.addEventListener('click', onClick)
  document.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  document.removeEventListener('click', onClick)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <dialog
    ref="dialog"
    class="xk-lightbox"
    aria-label="放大的图示"
    @cancel.prevent="hide"
    @click.self="hide"
  >
    <div class="xk-lightbox__bar">
      <button type="button" class="xk-lightbox__size" :aria-pressed="originalSize" @click="originalSize = !originalSize">{{ originalSize ? '适应窗口' : '原始尺寸' }}</button>
      <a v-if="src" class="xk-lightbox__original" :href="src" target="_blank" rel="noreferrer">打开原图</a>
      <button type="button" class="xk-lightbox__close" aria-label="关闭放大的图示" @click="hide">
        <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
      </button>
    </div>
    <div class="xk-lightbox__stage" :class="{ 'is-original-size': originalSize }" @click.self="hide">
      <img v-if="src" class="xk-lightbox__img" :src="src" :alt="alt">
    </div>
    <p v-if="caption" class="xk-lightbox__cap">{{ caption }}</p>
  </dialog>
</template>
