<script setup lang="ts">
import { withBase } from 'vitepress'
</script>

<template>
  <main id="xk-main" class="xk-lost">
    <div class="xk-lost__sheet">
      <div>
        <p class="xk-lost__code">404</p>
        <h1>这一页不在全书目录里</h1>
        <p>链接可能写错了，或者这一页已经换了位置。从全书目录或搜索重新找到它。</p>
        <div class="xk-lost__links">
          <a :href="withBase('/')">回到全书目录</a>
          <a :href="withBase('/theory/')">从开篇读起</a>
        </div>
      </div>
      <svg viewBox="0 0 320 240" aria-hidden="true" focusable="false">
        <g fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
          <circle cx="160" cy="120" r="88" stroke-dasharray="5 6" />
          <path d="M84 150 140 82l66 70" />
          <path d="M206 152 262 186" stroke-dasharray="4 7" />
        </g>
        <circle cx="84" cy="150" r="9" fill="var(--xk-sheet)" stroke="currentColor" stroke-width="1.6" />
        <circle cx="140" cy="82" r="9" fill="var(--xk-sheet)" stroke="currentColor" stroke-width="1.6" />
        <circle cx="206" cy="152" r="9" fill="var(--xk-marker)" stroke="currentColor" stroke-width="1.6" />
        <circle cx="262" cy="186" r="9" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="3 3" />
      </svg>
    </div>
  </main>
</template>
