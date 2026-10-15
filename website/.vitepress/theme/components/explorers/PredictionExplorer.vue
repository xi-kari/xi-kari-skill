<script setup lang="ts">
import { computed, ref, useId } from 'vue'

const id = useId()
const share = ref(50)
const result = computed(() => (0.1 + 0.7 * share.value / 100).toFixed(3))
</script>

<template>
  <section class="xk-model xk-pr" aria-label="预测与干预教学模型">
    <div class="xk-model__head">
      <span class="xk-tag xk-tag--assumed">教学模型</span>
      <p>原文教学设定：常态下 A₁、A₂ 进入 B 的概率均为 0.2；指定干预后分别变为 0.8 与 0.1。</p>
    </div>
    <div class="xk-model__stage">
      <label class="xk-pr__share" :for="`${id}-share`">
        <span>A₁ 在混合状态中的份额 p</span>
        <output :for="`${id}-share`">{{ share }}%</output>
      </label>
      <input
        :id="`${id}-share`"
        v-model.number="share"
        class="xk-range"
        type="range"
        min="0"
        max="100"
        step="1"
        :style="{ '--fill': `${share}%` }"
        :aria-valuetext="`${share}%`"
      >
      <div class="xk-scale" aria-hidden="true"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>
      <div class="xk-pr__bars">
        <div class="xk-pr__bar">
          <span>常态预测</span>
          <span class="xk-pr__track" aria-hidden="true"><span class="xk-pr__fill" style="transform: scaleX(.2)" /></span>
          <output>0.200</output>
        </div>
        <div class="xk-pr__bar">
          <span>指定干预后</span>
          <span class="xk-pr__track" aria-hidden="true"><span class="xk-pr__fill" :style="{ transform: `scaleX(${result})` }" /></span>
          <output aria-live="polite">{{ result }}</output>
        </div>
      </div>
      <p class="xk-pr__calc">计算：0.8 × p ＋ 0.1 × (1 − p) ＝ <strong>{{ result }}</strong>。常态结果保持相同，干预响应却随内部构成改变。</p>
    </div>
    <div class="xk-model__foot">
      <p>全部数值来自原文的形式教学例，不是现实测量。补入 p 只帮助这个指定问题，不自动解决长期演化与其他干预。</p>
    </div>
  </section>
</template>
