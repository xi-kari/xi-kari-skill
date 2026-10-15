<script setup lang="ts">
import { ref, useId } from 'vue'
import { withBase } from 'vitepress'

const stages = [
  { name: '收到回执', title: '消息回来了，后续决定还没有改变。', body: '记录能够证明有过接收。要判断有效反馈，还需要看这条返回通道是否实际改变后续状态、时序、概率或约束。', limit: '不能由“已收悉”推出问题已被纠正。' },
  { name: '改变决定', title: '返回信息进入了下一步。', body: '沿这条路线，反馈已经有了实际作用。它可能改善结果，也可能迟到、放大偏差或引起振荡；有效反馈不等于有益反馈。', limit: '不能由一次改变推出已经形成可保留的学习。' },
  { name: '保留并调用', title: '变化留下了载体，并在后来被使用。', body: '沿反馈介导学习这条路线，还须把后续预定任务与基线或替代过程比较，并核对相应因果依据。留档、调用与任务结果是不同环节。', limit: '不能只凭保留与调用宣布学习成立；学习成立也不自动证明净收益。' }
]

const id = useId()
const selected = ref(0)
/* counters re-key the segments that just switched on, so their arrival plays once */
const arrivals = ref([0, 0])

function choose(index: number) {
  if (index === selected.value) return
  const before = selected.value
  arrivals.value = arrivals.value.map((count, segment) => (index > segment && before <= segment ? count + 1 : count))
  selected.value = index
}

function move(event: KeyboardEvent) {
  if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (selected.value + (event.key === 'ArrowRight' ? 1 : 2)) % 3
  choose(next)
  ;(event.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>('[role="tab"]')[next]?.focus()
}

const nodes = [
  { x: 80, name: '返回信息', state: () => '有接收记录' },
  { x: 320, name: '后续决定', state: () => (selected.value > 0 ? '实际发生改变' : '尚未见改变') },
  { x: 560, name: '后续任务', state: () => (selected.value > 1 ? '更新被保留与调用' : '尚未见调用') }
]
</script>

<template>
  <section class="xk-model xk-fb" aria-label="反馈与学习关系示意">
    <div class="xk-model__head">
      <span class="xk-tag xk-tag--assumed">关系示意</span>
      <div class="xk-seg xk-fb__tabs" role="tablist" aria-label="查看不同情形" @keydown="move">
        <button
          v-for="(stage, i) in stages"
          :id="`${id}-tab-${i}`"
          :key="stage.name"
          type="button"
          role="tab"
          :aria-selected="selected === i"
          :aria-controls="`${id}-panel`"
          :tabindex="selected === i ? 0 : -1"
          @click="choose(i)"
        >{{ stage.name }}</button>
      </div>
    </div>
    <div class="xk-model__stage">
      <svg class="xk-fb__svg" viewBox="0 0 640 150" aria-hidden="true" focusable="false">
        <g v-for="segment in [0, 1]" :key="`segment-${segment}`">
          <path
            :key="`line-${segment}-${arrivals[segment]}`"
            class="xk-fb__line"
            :class="{ 'is-on': selected > segment, 'is-arriving': selected > segment && arrivals[segment] > 0 }"
            :d="`M${nodes[segment].x + 20} 50H${nodes[segment + 1].x - 26}`"
          />
          <path class="xk-fb__head" :class="{ 'is-on': selected > segment }" :d="`M${nodes[segment + 1].x - 28} 44l10 6-10 6z`" />
        </g>
        <g v-for="(node, i) in nodes" :key="node.name">
          <circle
            :key="`ring-${i}-${i > 0 ? arrivals[i - 1] : 0}`"
            class="xk-fb__ring"
            :class="{ 'is-pulse': i > 0 && selected >= i && arrivals[i - 1] > 0 }"
            :cx="node.x"
            cy="50"
            r="14"
          />
          <circle class="xk-fb__node" :class="{ 'is-on': i === 0 || selected >= i }" :cx="node.x" cy="50" r="14" />
          <text class="xk-fb__name" :class="{ 'is-on': i === 0 || selected >= i }" :x="node.x" y="98" text-anchor="middle">{{ node.name }}</text>
          <text class="xk-fb__state" :x="node.x" y="122" text-anchor="middle">{{ node.state() }}</text>
        </g>
      </svg>
    </div>
    <div :id="`${id}-panel`" class="xk-fb__panel" role="tabpanel" :aria-labelledby="`${id}-tab-${selected}`" tabindex="0">
      <Transition name="xk-swap" mode="out-in">
        <div :key="selected">
          <p class="xk-model__h">{{ stages[selected].title }}</p>
          <p>{{ stages[selected].body }}</p>
          <p class="xk-model__limit">{{ stages[selected].limit }}</p>
        </div>
      </Transition>
    </div>
    <div class="xk-model__foot">
      <p>原文关系示意：<a :href="withBase('/theory/part-03.html#section-3-3')">§3.3</a>、<a :href="withBase('/theory/part-06.html#section-6-3')">§6.3—6.4</a></p>
    </div>
  </section>
</template>
