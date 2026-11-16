<script setup lang="ts">
import { useLocale } from '../composables/locale'
const { t, isEnglish, localePath } = useLocale()
import { computed, nextTick, ref, watch } from 'vue'
import { useSharedOutline } from '../composables/outline'
import { usePrefs, type TextSize } from '../composables/prefs'

defineProps<{ open: boolean; isTheory: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { items, active } = useSharedOutline()
const prefs = usePrefs()
const sizes = computed<{ value: TextSize; text: string }[]>(() => [
  { value: 's', text: t('小', 'S') },
  { value: 'm', text: t('中', 'M') },
  { value: 'l', text: t('大', 'L') }
])

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
    window.prompt(t('复制本页链接', 'Copy page link'), location.href)
  }
  window.clearTimeout(timer)
  timer = window.setTimeout(() => { copied.value = false }, 2200)
}
</script>

<template>
  <aside id="xk-aside" class="xk-aside" :aria-label="t('本页目录与阅读设置', 'Page outline and reading settings')">
    <div class="xk-aside__scroll">
      <div class="xk-aside__head">
        <p class="xk-aside__title">{{ t('本页', 'On this page') }}</p>
        <button type="button" class="xk-tool xk-drawer-close" :aria-label="t('关闭', 'Close')" @click="emit('close')">
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </div>
      <nav class="xk-outline" :aria-label="t('本页分节', 'Page sections')">
        <ol v-if="items.length" ref="list">
          <li v-for="item in items" :key="item.id" :class="{ 'is-sub': item.level === 3 }">
            <a :href="`#${item.id}`" :class="{ 'is-active': item.id === active }" @click="emit('close')">
              <span v-if="item.no" class="xk-outline__no">{{ item.no }}</span>
              <span>{{ item.text }}</span>
            </a>
          </li>
        </ol>
        <p v-else class="xk-outline__empty">{{ t('本页没有分节。', 'This page has no subsections.') }}</p>
        <span v-if="items.length" class="xk-outline__marker" :style="markerStyle" aria-hidden="true" />
      </nav>
      <section class="xk-prefs" :aria-label="t('阅读设置', 'Reading settings')">
        <button
          v-if="isTheory"
          type="button"
          role="switch"
          class="xk-switch"
          :aria-checked="prefs.sourceOnly"
          @click="prefs.sourceOnly = !prefs.sourceOnly"
        >
          <span>{{ t('只看原文', 'Source text only') }}</span>
          <span class="xk-switch__track" aria-hidden="true" />
        </button>
        <div class="xk-pref">
          <span id="xk-pref-size" class="xk-pref__label">{{ t('字号', 'Text size') }}</span>
          <div class="xk-seg" role="group" aria-labelledby="xk-pref-size">
            <button v-for="size in sizes" :key="size.value" type="button" :aria-pressed="prefs.size === size.value" @click="prefs.size = size.value">{{ size.text }}</button>
          </div>
        </div>
        <div class="xk-pref">
          <span id="xk-pref-face" class="xk-pref__label">{{ t('正文字体', 'Text face') }}</span>
          <div class="xk-seg" role="group" aria-labelledby="xk-pref-face">
            <button type="button" :aria-pressed="prefs.body === 'sans'" @click="prefs.body = 'sans'">{{ t('黑体', 'Sans') }}</button>
            <button type="button" :aria-pressed="prefs.body === 'song'" @click="prefs.body = 'song'">{{ t('宋体', 'Serif') }}</button>
          </div>
        </div>
        <button type="button" class="xk-copy" :class="{ 'is-done': copied }" aria-live="polite" @click="copyLink">
          {{ copied ? t('已复制本页链接', 'Link copied') : t('复制本页链接', 'Copy page link') }}
        </button>
      </section>
    </div>
  </aside>
</template>
