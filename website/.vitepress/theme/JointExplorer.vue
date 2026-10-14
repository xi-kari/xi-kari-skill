<script setup lang="ts">
import { ref, computed } from 'vue'
const deadline = ref(1)
const futureCapacity = ref(1)
const possible = computed(() => deadline.value === 2 && futureCapacity.value >= 1)
</script>

<template>
  <section class="model-explorer" aria-label="联合可行性教学模型">
    <p class="model-setting">原文教学设定：任务 A、B 各需 1 个时段，共享同一执行资源；第一期容量为 1。</p>
    <div class="model-controls">
      <label>两项任务的截止时间<select v-model.number="deadline"><option :value="1">第一期结束</option><option :value="2">允许延至第二期</option></select></label>
      <label>第二期的新增容量<select v-model.number="futureCapacity"><option :value="0">0 个时段</option><option :value="1">1 个时段</option><option :value="2">2 个时段</option></select></label>
    </div>
    <div class="capacity-track" aria-hidden="true"><div><span>第一期</span><strong>A</strong><small>容量 1</small></div><div :class="{ 'available-period': possible }"><span>第二期</span><strong>{{ possible ? 'B' : '—' }}</strong><small>{{ deadline === 1 ? '已经超过期限' : `容量 ${futureCapacity}` }}</small></div></div>
    <div class="model-result" aria-live="polite"><strong>{{ possible ? '在这些条件下，两项任务可以安排。' : '在这些条件下，不能同时按期完成。' }}</strong><p>{{ deadline === 1 ? '两项任务都挤在第一期，需要 2 个时段，但容量只有 1。增加第二期容量，不能补回已经错过的期限。' : futureCapacity === 0 ? '截止时间已调整，但第二期没有新增容量，仍然缺少完成第二项任务的时段。' : '第一期完成 A，第二期完成 B。这里改变了原定期限，因此回答的是条件调整后的可行性。' }}</p></div>
    <p class="source-note">离散教学模型；调整期限只是查看另一种条件，不代表现实中已经获得改期权限。</p>
  </section>
</template>
