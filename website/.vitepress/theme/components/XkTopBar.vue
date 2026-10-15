<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useData, withBase } from 'vitepress'
import XkMark from './XkMark.vue'
import { flipTheme } from '../composables/transitions'
import { pageHref, routeOf } from '../composables/nav'
import { topLinks as links } from '../composables/links'

defineProps<{ progress: number; navOpen: boolean; asideOpen: boolean; hasAside: boolean; hasNav: boolean }>()
const emit = defineEmits<{ (e: 'toggle-nav'): void; (e: 'toggle-aside'): void; (e: 'search'): void }>()

const { isDark, page } = useData()
const route = computed(() => routeOf(page.value.relativePath))
const shortcut = ref('Ctrl K')
onMounted(() => {
  if (/Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent)) shortcut.value = '⌘ K'
})
/* pass the ref itself: inside the template isDark is already unwrapped */
const toggleTheme = (event: MouseEvent) => flipTheme(event, isDark)
</script>

<template>
  <header class="xk-topbar">
    <div class="xk-topbar__inner">
      <button
        v-if="hasNav"
        type="button"
        class="xk-tool xk-topbar__menu"
        aria-label="全书目录"
        aria-controls="xk-nav"
        :aria-expanded="navOpen"
        @click="emit('toggle-nav')"
      >
        <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6.5h16M4 12h16M4 17.5h10" /></svg>
      </button>
      <a class="xk-brand" :href="withBase('/')" aria-label="条件结构与转化论，回到首页">
        <XkMark class="xk-brand__mark" />
        <span class="xk-brand__name xk-fang">条件结构与转化论</span>
        <span class="xk-brand__author">Xikari</span>
      </a>
      <nav class="xk-topnav" aria-label="栏目">
        <a
          v-for="item in links"
          :key="item.link"
          :href="pageHref(item.link)"
          :aria-current="item.match(route) ? 'page' : undefined"
        >{{ item.text }}</a>
      </nav>
      <div class="xk-topbar__tools">
        <button type="button" class="xk-search-btn" aria-label="搜索全书" @click="emit('search')">
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
          <span>搜索概念与原文</span>
          <kbd>{{ shortcut }}</kbd>
        </button>
        <button
          v-if="hasAside"
          type="button"
          class="xk-tool xk-tool--aside"
          aria-label="本页目录与阅读设置"
          aria-controls="xk-aside"
          :aria-expanded="asideOpen"
          @click="emit('toggle-aside')"
        >
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6.5h11M9 12h11M9 17.5h7" /><circle cx="4.5" cy="6.5" r="1" /><circle cx="4.5" cy="12" r="1" /><circle cx="4.5" cy="17.5" r="1" /></svg>
        </button>
        <button
          type="button"
          class="xk-tool"
          :aria-label="isDark ? '切换到浅色' : '切换到深色'"
          :title="isDark ? '切换到浅色' : '切换到深色'"
          @click="toggleTheme"
        >
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="8" />
            <path d="M12 4a8 8 0 0 0 0 16Z" fill="currentColor" stroke="none" />
            <path d="M12 8.5h4M12 12h5M12 15.5h4" stroke-width="1.2" />
          </svg>
        </button>
        <a class="xk-tool xk-tool--github" href="https://github.com/xi-kari/xi-kari-skill" target="_blank" rel="noreferrer" aria-label="GitHub 仓库">
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 19c-4 1.4-4-2-6-2.4m12 4.4v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21" /></svg>
        </a>
      </div>
    </div>
    <div class="xk-progress" aria-hidden="true"><span :style="{ transform: `scaleX(${progress})` }" /></div>
  </header>
</template>
