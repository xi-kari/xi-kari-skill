<script setup lang="ts">
import { ref, computed } from 'vue'
const share = ref(50)
const result = computed(() => (0.1 + 0.7 * share.value / 100).toFixed(3))
</script>

<template>
  <section class="model-explorer" aria-label="预测与干预教学模型">
    <p class="model-setting">原文教学设定：常态下 A₁、A₂ 进入 B 的概率均为 0.2；指定干预后分别变为 0.8 与 0.1。</p>
    <label class="share-control" for="share-input">A₁ 在混合状态中的份额 p：<strong>{{ share }}%</strong></label>
    <input id="share-input" type="range" min="0" max="100" step="1" v-model.number="share" :aria-valuetext="`${share}%`">
    <div class="probability-bars">
      <div><span>常态预测</span><div class="bar-track"><div style="transform:scaleX(.2)"></div></div><output>0.200</output></div>
      <div><span>指定干预后</span><div class="bar-track"><div :style="{ transform: `scaleX(${result})` }"></div></div><output aria-live="polite">{{ result }}</output></div>
    </div>
    <p class="model-result">计算：0.8 × p ＋ 0.1 × (1 − p) ＝ <strong>{{ result }}</strong>。常态结果保持相同，干预响应却随内部构成改变。</p>
    <p class="source-note">全部数值来自原文的形式教学例，不是现实测量。补入 p 只帮助这个指定问题，不自动解决长期演化与其他干预。</p>
  </section>
</template>
