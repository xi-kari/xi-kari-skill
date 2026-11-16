<script setup lang="ts">
import { useLocale } from '../composables/locale'
const { t, isEnglish, localePath } = useLocale()
import { computed } from 'vue'
import { useData } from 'vitepress'
import XkPosition from './XkPosition.vue'
import { sheetNo, useNav } from '../composables/nav'

const { frontmatter } = useData()
const { route, current, currentGroup, lessonsOn } = useNav()

const no = computed(() => current.value?.no || sheetNo(route.value) || '—')
const group = computed(() => currentGroup.value?.text || t('原文', 'Source text'))
const lessons = computed(() => lessonsOn(route.value))
const length = computed(() => {
  if (isEnglish.value) {
    const words = Number(frontmatter.value.xkWords || 0)
    return words ? `About ${words.toLocaleString('en')} words, ${Math.max(1, Math.round(words / 220))} min` : ''
  }
  const chars = Number(frontmatter.value.xkChars || 0)
  if (!chars) return ''
  const minutes = Math.max(1, Math.round(chars / 380))
  const amount = chars >= 10000 ? `${(chars / 10000).toFixed(1).replace(/\.0$/, '')} 万字` : `${Math.max(100, Math.round(chars / 100) * 100)} 字`
  return `约 ${amount}，${minutes} 分钟`
})
</script>

<template>
  <header class="xk-tb" :aria-label="t('本篇信息', 'Page information')">
    <div class="xk-tb__no">
      <span class="xk-tb__label">{{ t('编号', 'Number') }}</span>
      <span class="xk-tb__value">{{ no }}</span>
    </div>
    <div>
      <span class="xk-tb__label">{{ t('所属', 'Part') }}</span>
      <span class="xk-tb__value">{{ group }}</span>
    </div>
    <div v-if="length">
      <span class="xk-tb__label">{{ t('篇幅', 'Length') }}</span>
      <span class="xk-tb__value xk-tb__nowrap">{{ length }}</span>
    </div>
    <div class="xk-tb__lessons">
      <span class="xk-tb__label">{{ t('讲解', 'Notes') }}</span>
      <span class="xk-tb__value xk-tb__nowrap">{{ lessons ? t(`${lessons} 处`, `${lessons}`) : t('暂无', 'None yet') }}</span>
    </div>
    <div class="xk-tb__rose"><XkPosition :no="no" /></div>
  </header>
</template>
