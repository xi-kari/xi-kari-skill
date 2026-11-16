<script setup lang="ts">
import { useLocale } from '../composables/locale'
const { t, isEnglish, localePath } = useLocale()
import { withBase } from 'vitepress'
import XkBookRose from './XkBookRose.vue'
</script>

<template>
  <main id="xk-main" class="xk-lost" tabindex="-1">
    <div class="xk-lost__sheet">
      <div class="xk-lost__text">
        <p class="xk-lost__code">404</p>
        <h1>{{ t('这一页不在全书目录里', 'This page is not in the book') }}</h1>
        <p>{{ t('链接可能写错了，或者这一页已经换了位置。从全书目录或搜索重新找到它。', 'The link may be incorrect or the page may have moved. Use the contents or search to find it.') }}</p>
        <div class="xk-lost__links">
          <a class="xk-sign xk-sign--go" :href="withBase(localePath('/'))">{{ t('回到全书目录', 'Back to the contents') }}</a>
          <a class="xk-sign xk-sign--plain" :href="withBase(localePath('/theory/'))">{{ t('从开篇读起', 'Start reading') }}</a>
        </div>
      </div>
      <XkBookRose class="xk-lost__rose" />
    </div>
  </main>
</template>
