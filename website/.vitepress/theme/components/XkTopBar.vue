<script setup lang="ts">
import { useLocale, useLanguageSwitch } from '../composables/locale'
const { t, isEnglish, localePath } = useLocale()
import { computed, onMounted, ref } from 'vue'
import { useData, withBase } from 'vitepress'
import XkMark from './XkMark.vue'
import { flipTheme } from '../composables/transitions'
import { pageHref, routeOf, sheetNo, useNav } from '../composables/nav'
import { projectHome, useTopLinks } from '../composables/links'
import { useSharedOutline } from '../composables/outline'
import { usePrefs } from '../composables/prefs'

defineProps<{ progress: number; navOpen: boolean; asideOpen: boolean; hasAside: boolean; hasNav: boolean; isTheory: boolean }>()
const emit = defineEmits<{ (e: 'toggle-nav'): void; (e: 'toggle-aside'): void; (e: 'search'): void }>()

const { isDark, page } = useData()
const links = useTopLinks()
const languageLink = useLanguageSwitch()
const route = computed(() => routeOf(page.value.relativePath))
const shortcut = ref('Ctrl K')
onMounted(() => {
  if (/Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent)) shortcut.value = '⌘ K'
})
/* pass the ref itself: inside the template isDark is already unwrapped */
const toggleTheme = (event: MouseEvent) => flipTheme(event, isDark)

/* The locator strip: which sheet this is and which section is being read. It stands in
   for the page outline wherever the outline is folded into a drawer. */
const { current } = useNav()
const { items, active } = useSharedOutline()
const prefs = usePrefs()
const sheet = computed(() => current.value?.no || sheetNo(route.value))
const here = computed(() => {
  const section = items.value.find((item) => item.id === active.value)
  return section ? { no: section.no, text: section.text } : { no: '', text: current.value?.title || page.value.title }
})
</script>

<template>
  <header class="xk-topbar">
    <div class="xk-topbar__inner">
      <button
        v-if="hasNav"
        type="button"
        class="xk-tool xk-topbar__menu"
        :aria-label="t('全书目录', 'Book contents')"
        aria-controls="xk-nav"
        :aria-expanded="navOpen"
        @click="emit('toggle-nav')"
      >
        <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6.5h16M4 12h16M4 17.5h10" /></svg>
      </button>
      <a class="xk-brand" :href="withBase(localePath('/'))" :aria-label="t('条件结构与转化论，回到首页', 'Xikari reader \u2014 home')">
        <XkMark class="xk-brand__mark" />
        <span class="xk-brand__name xk-display">{{ t('条件结构与转化论', 'Xikari Reader') }}</span>
        <span class="xk-brand__author">Xikari</span>
      </a>
      <nav class="xk-topnav" :aria-label="t('栏目', 'Sections')">
        <a
          v-for="item in links"
          :key="item.link"
          :href="pageHref(item.link)"
          :aria-current="item.match(route) ? 'page' : undefined"
        >{{ item.text }}</a>
      </nav>
      <div class="xk-topbar__tools">
        <a class="xk-tool xk-tool--language" :href="pageHref(languageLink)" :hreflang="isEnglish ? 'zh-CN' : 'en'" :aria-label="t('切换到英文，保留对应章节', 'Read the corresponding Chinese section')">{{ isEnglish ? '中文' : 'EN' }}</a>
        <a class="xk-tool xk-tool--home" :href="projectHome" target="_self">{{ t('项目主页', 'Project') }}</a>
        <button type="button" class="xk-search-btn" :aria-label="t('搜索全书', 'Search the book')" @click="emit('search')">
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
          <span>{{ t('搜索概念与原文', 'Search the book') }}</span>
          <kbd>{{ shortcut }}</kbd>
        </button>
        <button
          v-if="hasAside"
          type="button"
          class="xk-tool xk-tool--aside"
          :aria-label="t('本页目录与阅读设置', 'Page outline and reading settings')"
          aria-controls="xk-aside"
          :aria-expanded="asideOpen"
          @click="emit('toggle-aside')"
        >
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6.5h11M9 12h11M9 17.5h7" /><circle cx="4.5" cy="6.5" r="1" /><circle cx="4.5" cy="12" r="1" /><circle cx="4.5" cy="17.5" r="1" /></svg>
        </button>
        <button
          type="button"
          class="xk-tool"
          :aria-label="isDark ? t('切换到浅色', 'Use light theme') : t('切换到深色', 'Use dark theme')"
          :title="isDark ? t('切换到浅色', 'Use light theme') : t('切换到深色', 'Use dark theme')"
          @click="toggleTheme"
        >
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="8" />
            <path d="M12 4a8 8 0 0 0 0 16Z" fill="currentColor" stroke="none" />
            <path d="M12 8.5h4M12 12h5M12 15.5h4" stroke-width="1.2" />
          </svg>
        </button>
        <a class="xk-tool xk-tool--github" href="https://github.com/xi-kari/xi-kari-skill" target="_blank" rel="noreferrer" :aria-label="t('GitHub 仓库', 'GitHub repository')">
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 19c-4 1.4-4-2-6-2.4m12 4.4v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21" /></svg>
        </a>
      </div>
    </div>
    <div v-if="hasAside" class="xk-locator">
      <span class="xk-locator__no" aria-hidden="true">{{ sheet || '·' }}</span>
      <button type="button" class="xk-locator__where" aria-controls="xk-aside" :aria-expanded="asideOpen" @click="emit('toggle-aside')">
        <span class="xk-sr">{{ t('本页目录，正在读：', 'Page outline, reading:') }}</span>
        <span v-if="here.no" class="xk-locator__sec">{{ here.no }}</span>
        <span class="xk-locator__text">{{ here.text }}</span>
        <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
      </button>
      <button
        v-if="isTheory"
        type="button"
        role="switch"
        class="xk-switch xk-locator__switch"
        :aria-checked="prefs.sourceOnly"
        @click="prefs.sourceOnly = !prefs.sourceOnly"
      >
        <span>{{ t('只看原文', 'Source text only') }}</span>
        <span class="xk-switch__track" aria-hidden="true" />
      </button>
    </div>
    <div class="xk-progress" aria-hidden="true"><span :style="{ transform: `scaleX(${progress})` }" /></div>
  </header>
</template>
