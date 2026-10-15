<script setup lang="ts">
import { computed } from 'vue'
import { useData } from 'vitepress'
import XkSigil from './XkSigil.vue'
import { sheetNo, useNav } from '../composables/nav'

const { frontmatter } = useData()
const { route, current, currentGroup, lessonsOn } = useNav()

const no = computed(() => current.value?.no || sheetNo(route.value) || '—')
const group = computed(() => currentGroup.value?.text || '原文')
const lessons = computed(() => lessonsOn(route.value))
const length = computed(() => {
  const chars = Number(frontmatter.value.xkChars || 0)
  if (!chars) return ''
  const minutes = Math.max(1, Math.round(chars / 380))
  const amount = chars >= 10000 ? `${(chars / 10000).toFixed(1).replace(/\.0$/, '')} 万字` : `${Math.max(100, Math.round(chars / 100) * 100)} 字`
  return `约 ${amount}，${minutes} 分钟`
})
</script>

<template>
  <header class="xk-tb" aria-label="本篇信息">
    <div class="xk-tb__no">
      <span class="xk-tb__label">编号</span>
      <span class="xk-tb__value">{{ no }}</span>
    </div>
    <div>
      <span class="xk-tb__label">所属</span>
      <span class="xk-tb__value">{{ group }}</span>
    </div>
    <div v-if="length">
      <span class="xk-tb__label">篇幅</span>
      <span class="xk-tb__value xk-tb__nowrap">{{ length }}</span>
    </div>
    <div class="xk-tb__lessons">
      <span class="xk-tb__label">讲解</span>
      <span class="xk-tb__value xk-tb__nowrap">{{ lessons ? `${lessons} 处` : '暂无' }}</span>
    </div>
    <div class="xk-tb__sigil"><XkSigil :seed="`xk-${no}`" /></div>
  </header>
</template>
