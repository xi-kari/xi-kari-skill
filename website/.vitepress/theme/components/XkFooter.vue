<script setup lang="ts">
import { withBase } from 'vitepress'
import { pageHref } from '../composables/nav'
</script>

<template>
  <footer class="xk-footer">
    <div class="xk-footer__inner">
      <p>《Xikari-条件结构与转化论》，Xikari 著，2026 年 10 月。讲解与案例是辅助阅读的内容，引用定义请回到原文节号。</p>
      <nav aria-label="页脚链接">
        <a :href="pageHref('/downloads')">下载与引用</a>
        <a :href="withBase('/guide/')">使用指南</a>
        <a href="https://github.com/xi-kari/xi-kari-skill" target="_blank" rel="noreferrer">GitHub</a>
        <a :href="withBase('/THIRD_PARTY_NOTICES.txt')">第三方许可</a>
      </nav>
    </div>
  </footer>
</template>
