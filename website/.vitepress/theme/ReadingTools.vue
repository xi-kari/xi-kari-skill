<script setup lang="ts">
import { computed, ref } from 'vue'
import { useData } from 'vitepress'
const { page } = useData()
const large = ref(false)
const copied = ref(false)
const isTheory = computed(() => page.value.relativePath.startsWith('theory/'))
function resize() {
  large.value = !large.value
  document.documentElement.classList.toggle('reading-large', large.value)
}
async function copyLink() {
  try {
    await navigator.clipboard.writeText(location.href)
    copied.value = true
    window.setTimeout(() => { copied.value = false }, 2200)
  } catch {
    copied.value = false
    window.prompt('复制本页链接', location.href)
  }
}
</script>

<template>
  <div class="reading-tools">
    <span>{{ isTheory ? 'Xikari 著 · 理论原文' : 'Xikari · 阅读与理解' }}</span>
    <div class="reading-actions">
      <button type="button" :aria-pressed="large" @click="resize" aria-label="切换大字号">字号 <span aria-hidden="true">A<span class="big-a">A</span></span></button>
      <button type="button" @click="copyLink" aria-live="polite">{{ copied ? '链接已复制' : '复制链接' }}</button>
    </div>
  </div>
</template>
