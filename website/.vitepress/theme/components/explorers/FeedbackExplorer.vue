<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { withBase } from 'vitepress'
import { useLocale } from '../../composables/locale'

const { t, localePath } = useLocale()

const stages = computed(() => [
  { name: t('收到回执', 'Receipt received'), title: t('消息回来了，后续决定还没有改变。', 'A message has returned; the later decision has not changed.'), body: t('记录能够证明有过接收。要判断有效反馈，还需要看这条返回通道是否实际改变后续状态、时序、概率或约束。', 'A record can establish receipt. To identify effective feedback, check whether this return channel actually changes a later state, timing, probability or constraint.'), limit: t('不能由“已收悉”推出问题已被纠正。', 'Acknowledgement does not establish that the problem has been corrected.') },
  { name: t('改变决定', 'Decision changed'), title: t('返回信息进入了下一步。', 'The returned information affects what happens next.'), body: t('沿这条路线，反馈已经有了实际作用。它可能改善结果，也可能迟到、放大偏差或引起振荡；有效反馈不等于有益反馈。', 'Along this route, feedback has had an actual effect. It may improve the result, arrive too late, amplify a deviation or cause oscillation. Effective feedback is not necessarily beneficial feedback.'), limit: t('不能由一次改变推出已经形成可保留的学习。', 'One change does not establish learning that can be retained.') },
  { name: t('保留并调用', 'Retained and used'), title: t('变化留下了载体，并在后来被使用。', 'The change persists in a carrier and is used later.'), body: t('沿反馈介导学习这条路线，还须把后续预定任务与基线或替代过程比较，并核对相应因果依据。留档、调用与任务结果是不同环节。', 'For feedback-mediated learning, the later specified task must also be compared with a baseline or alternative process, with the relevant causal evidence checked. Recording, use and task results are distinct steps.'), limit: t('不能只凭保留与调用宣布学习成立；学习成立也不自动证明净收益。', 'Retention and use alone do not establish learning; learning does not automatically establish a net benefit.') }
])

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

const nodes = computed(() => [
  { x: 80, name: t('返回信息', 'Returned information'), state: () => t('有接收记录', 'Receipt recorded') },
  { x: 320, name: t('后续决定', 'Later decision'), state: () => (selected.value > 0 ? t('实际发生改变', 'Changed') : t('尚未见改变', 'No change observed')) },
  { x: 560, name: t('后续任务', 'Later task'), state: () => (selected.value > 1 ? t('更新被保留与调用', 'Update retained and used') : t('尚未见调用', 'No use observed')) }
])
</script>

<template>
  <section class="xk-model xk-fb" :aria-label="t('反馈与学习关系示意', 'Feedback and learning diagram')">
    <div class="xk-model__head">
      <span class="xk-tag xk-tag--assumed">{{ t('关系示意', 'Relationship diagram') }}</span>
      <div class="xk-seg xk-fb__tabs" role="tablist" :aria-label="t('查看不同情形', 'Explore different situations')" @keydown="move">
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
      <p>{{ t('原文关系示意：', 'Relations in the source: ') }}<a :href="withBase(localePath('/theory/part-03.html#section-3-3'))">§3.3</a>{{ t('、', ', ') }}<a :href="withBase(localePath('/theory/part-06.html#section-6-3'))">§6.3—6.4</a></p>
    </div>
  </section>
</template>
