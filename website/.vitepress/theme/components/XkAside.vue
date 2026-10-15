<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useOutline } from '../composables/outline'
import { usePrefs, type TextSize } from '../composables/prefs'

defineProps<{ open: boolean; isTheory: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { items, active } = useOutline()
const prefs = usePrefs()
const sizes: { value: TextSize; text: string }[] = [
  { value: 's', text: '小' },
  { value: 'm', text: '中' },
  { value: 'l', text: '大' }
]

const list = ref<HTMLElement>()
const markerY = ref(0)
const markerShown = ref(false)
function placeMarker() {
  const link = list.value?.querySelector<HTMLElement>('a.is-active')
  markerShown.value = !!link
  if (link) markerY.value = link.offsetTop + (link.offsetHeight - 22) / 2
}
watch([active, items], () => nextTick(placeMarker))
const markerStyle = computed(() => ({ transform: `translateY(${markerY.value}px)`, opacity: markerShown.value ? 1 : 0 }))

const copied = ref(false)
let timer = 0
async function copyLink() {
  try {
    await navigator.clipboard.writeText(location.href)
    copied.value = true
  } catch {
    window.prompt('复制本页链接', location.href)
  }
  window.clearTimeout(timer)
  timer = window.setTimeout(() => { copied.value = false }, 2200)
}
</script>

<template>
  <aside id="xk-aside" class="xk-aside" aria-label="本页目录与阅读设置">
    <div class="xk-aside__scroll">
      <div class="xk-aside__head">
        <p class="xk-aside__title">本页</p>
        <button type="button" class="xk-tool xk-drawer-close" aria-label="关闭" @click="emit('close')">
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </div>
      <nav class="xk-outline" aria-label="本页分节">
        <ol v-if="items.length" ref="list">
          <li v-for="item in items" :key="item.id" :class="{ 'is-sub': item.level === 3 }">
            <a :href="`#${item.id}`" :class="{ 'is-active': item.id === active }" @click="emit('close')">
              <span v-if="item.no" class="xk-outline__no">{{ item.no }}</span>
              <span>{{ item.text }}</span>
              <span v-if="item.lesson" class="xk-nav__dot" title="此节之后有讲解" />
            </a>
          </li>
        </ol>
        <p v-else class="xk-outline__empty">本页没有分节。</p>
        <span v-if="items.length" class="xk-outline__marker" :style="markerStyle" aria-hidden="true" />
      </nav>
      <section class="xk-prefs" aria-label="阅读设置">
        <button
          v-if="isTheory"
          type="button"
          role="switch"
          class="xk-switch"
          :aria-checked="prefs.sourceOnly"
          @click="prefs.sourceOnly = !prefs.sourceOnly"
        >
          <span>只看原文</span>
          <span class="xk-switch__track" aria-hidden="true" />
        </button>
        <div class="xk-pref">
          <span id="xk-pref-size" class="xk-pref__label">字号</span>
          <div class="xk-seg" role="group" aria-labelledby="xk-pref-size">
            <button v-for="size in sizes" :key="size.value" type="button" :aria-pressed="prefs.size === size.value" @click="prefs.size = size.value">{{ size.text }}</button>
          </div>
        </div>
        <div class="xk-pref">
          <span id="xk-pref-face" class="xk-pref__label">正文字体</span>
          <div class="xk-seg" role="group" aria-labelledby="xk-pref-face">
            <button type="button" :aria-pressed="prefs.body === 'sans'" @click="prefs.body = 'sans'">黑体</button>
            <button type="button" :aria-pressed="prefs.body === 'fang'" @click="prefs.body = 'fang'">仿宋</button>
          </div>
        </div>
        <button type="button" class="xk-copy" :class="{ 'is-done': copied }" aria-live="polite" @click="copyLink">
          {{ copied ? '已复制本页链接' : '复制本页链接' }}
        </button>
      </section>
    </div>
  </aside>
</template>
