<script setup lang="ts">
import { useLocale } from '../composables/locale'
const { t, isEnglish, localePath } = useLocale()
import { withBase } from 'vitepress'
import { pageHref } from '../composables/nav'
import { projectHome } from '../composables/links'
</script>

<template>
  <footer class="xk-footer">
    <div class="xk-footer__inner">
      <p>{{ t('《Xikari-条件结构与转化论》，Xikari 著，v3.0，2026 年 11 月。讲解与案例是辅助阅读的内容，引用定义请回到原文节号。', 'On Conditions, Structure, and Transformation, by Xikari. Reading notes and cases support the text; cite the original section for definitions. The Chinese text governs the English reference edition.') }}</p>
      <nav :aria-label="t('页脚链接', 'Footer links')">
        <a :href="projectHome" target="_self">{{ t('项目主页', 'Project') }}</a>
        <a :href="pageHref(localePath('/downloads'))">{{ t('下载与引用', 'Downloads and citation') }}</a>
        <a :href="withBase(localePath('/guide/'))">{{ t('使用指南', 'Reader guide') }}</a>
        <a href="https://github.com/xi-kari/xi-kari-skill" target="_blank" rel="noreferrer">GitHub</a>
        <a :href="withBase('/THIRD_PARTY_NOTICES.txt')">{{ t('第三方许可', 'Third-party licenses') }}</a>
      </nav>
    </div>
  </footer>
</template>
