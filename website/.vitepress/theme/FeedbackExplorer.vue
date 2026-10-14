<script setup lang="ts">
import { ref } from 'vue'
import { withBase } from 'vitepress'
const selected = ref(0)
const stages = [
  { name: '收到回执', title: '消息回来了，后续决定还没有改变。', body: '记录能够证明有过接收。要判断有效反馈，还需要看这条返回通道是否实际改变后续状态、时序、概率或约束。', limit: '不能由“已收悉”推出问题已被纠正。' },
  { name: '改变决定', title: '返回信息进入了下一步。', body: '沿这条路线，反馈已经有了实际作用。它可能改善结果，也可能迟到、放大偏差或引起振荡；有效反馈不等于有益反馈。', limit: '不能由一次改变推出已经形成可保留的学习。' },
  { name: '保留并调用', title: '变化留下了载体，并在后来被使用。', body: '沿反馈介导学习这条路线，还须把后续预定任务与基线或替代过程比较，并核对相应因果依据。留档、调用与任务结果是不同环节。', limit: '不能只凭保留与调用宣布学习成立；学习成立也不自动证明净收益。' }
]
function move(event: KeyboardEvent) {
  if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  selected.value = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (selected.value + (event.key === 'ArrowRight' ? 1 : 2)) % 3
  ;(event.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>('[role="tab"]')[selected.value]?.focus()
}
</script>

<template>
  <section class="feedback-explorer" aria-label="反馈与学习关系示意">
    <div class="explorer-tabs" role="tablist" aria-label="查看不同情形" @keydown="move">
      <button v-for="(stage, i) in stages" :key="stage.name" :id="`feedback-tab-${i}`" type="button" role="tab" :aria-selected="selected === i" :tabindex="selected === i ? 0 : -1" aria-controls="feedback-panel" @click="selected = i">{{ stage.name }}</button>
    </div>
    <div class="signal-path" aria-hidden="true">
      <div class="signal-node active"><span class="node-dot"></span><strong>返回信息</strong><small>有接收记录</small></div>
      <span class="signal-link" :class="{ active: selected > 0 }">→</span>
      <div class="signal-node" :class="{ active: selected > 0 }"><span class="node-dot"></span><strong>后续决定</strong><small>{{ selected > 0 ? '实际发生改变' : '尚未见改变' }}</small></div>
      <span class="signal-link" :class="{ active: selected > 1 }">→</span>
      <div class="signal-node" :class="{ active: selected > 1 }"><span class="node-dot"></span><strong>后续任务</strong><small>{{ selected > 1 ? '更新被保留与调用' : '尚未见调用' }}</small></div>
    </div>
    <div id="feedback-panel" role="tabpanel" :aria-labelledby="`feedback-tab-${selected}`" tabindex="0" class="explorer-explanation">
      <h3>{{ stages[selected].title }}</h3>
      <p>{{ stages[selected].body }}</p>
      <p class="explorer-limit">{{ stages[selected].limit }}</p>
    </div>
    <p class="figure-source">原文关系示意 · <a :href="withBase('/theory/part-03.html#section-3-3')">§3.3</a>、<a :href="withBase('/theory/part-06.html#section-6-3')">§6.3—6.4</a></p>
  </section>
</template>
