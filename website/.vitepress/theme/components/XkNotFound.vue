<script setup lang="ts">
import { withBase } from 'vitepress'
import XkBookRose from './XkBookRose.vue'
</script>

<template>
  <main id="xk-main" class="xk-lost" tabindex="-1">
    <div class="xk-lost__sheet">
      <div class="xk-lost__text">
        <p class="xk-lost__code">404</p>
        <h1>这一页不在全书目录里</h1>
        <p>链接可能写错了，或者这一页已经换了位置。从全书目录或搜索重新找到它。</p>
        <div class="xk-lost__links">
          <a class="xk-sign xk-sign--go" :href="withBase('/')">回到全书目录</a>
          <a class="xk-sign xk-sign--plain" :href="withBase('/theory/')">从开篇读起</a>
        </div>
      </div>
      <XkBookRose class="xk-lost__rose" />
    </div>
  </main>
</template>
