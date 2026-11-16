<script setup lang="ts">
import { useLocale } from '../composables/locale'
const { t, isEnglish, localePath } = useLocale()
import { pageHref, useNav } from '../composables/nav'

const { prev, next } = useNav()
</script>

<template>
  <nav v-if="prev || next" class="xk-pager" :aria-label="t('上一篇与下一篇', 'Previous and next page')">
    <a v-if="prev" class="xk-pager__prev" :href="pageHref(prev.link)">
      <span class="xk-pager__dir">{{ t('上一篇', 'Previous') }}</span>
      <span class="xk-pager__no">{{ prev.no }}</span>
      <span class="xk-pager__title">{{ prev.title }}</span>
    </a>
    <a v-if="next" class="xk-pager__next" :href="pageHref(next.link)">
      <span class="xk-pager__dir">{{ t('下一篇', 'Next') }}</span>
      <span class="xk-pager__title">{{ next.title }}</span>
      <span class="xk-pager__no">{{ next.no }}</span>
    </a>
  </nav>
</template>
