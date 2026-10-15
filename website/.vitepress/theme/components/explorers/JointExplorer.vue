<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, useId, watch } from 'vue'

const id = useId()
const deadline = ref(1)
const futureCapacity = ref(1)
const possible = computed(() => deadline.value === 2 && futureCapacity.value >= 1)
const secondOpen = computed(() => deadline.value === 2)

const track = ref<HTMLElement>()
const firstBox = ref<HTMLElement>()
const secondBox = ref<HTMLElement>()
const placedA = ref('')
const placedB = ref('')
const ready = ref(false)

/* Task blocks are positioned over the drawing so they glide between periods. */
function place() {
  const root = track.value
  const one = firstBox.value
  const two = secondBox.value
  if (!root || !one || !two) return
  const origin = root.getBoundingClientRect()
  const slotOf = (box: HTMLElement) => box.querySelector<HTMLElement>('.xk-jf__slot')?.getBoundingClientRect()
  const firstSlot = slotOf(one)!
  placedA.value = `translate(${firstSlot.left - origin.left}px, ${firstSlot.top - origin.top}px)`
  let x: number
  let y = firstSlot.top - origin.top
  if (possible.value) {
    const slot = slotOf(two)!
    x = slot.left - origin.left
    y = slot.top - origin.top
  } else if (deadline.value === 1) {
    const box = one.getBoundingClientRect()
    x = box.right - origin.left - 22
  } else {
    const box = two.getBoundingClientRect()
    x = box.left - origin.left + 12
    y = box.top - origin.top + 12
  }
  placedB.value = `translate(${x}px, ${y}px)`
  ready.value = true
}

watch([deadline, futureCapacity], () => nextTick(place))
onMounted(() => {
  place()
  window.addEventListener('resize', place)
})
onUnmounted(() => window.removeEventListener('resize', place))
</script>

<template>
  <section class="xk-model xk-jf" aria-label="联合可行性教学模型">
    <div class="xk-model__head">
      <span class="xk-tag xk-tag--assumed">教学模型</span>
      <p>原文教学设定：任务 A、B 各需 1 个时段，共享同一执行资源；第一期容量为 1。</p>
    </div>
    <div class="xk-model__stage">
      <div class="xk-model__controls">
        <div class="xk-model__control">
          <span :id="`${id}-deadline`" class="xk-model__label">两项任务的截止时间</span>
          <div class="xk-seg" role="radiogroup" :aria-labelledby="`${id}-deadline`">
            <button type="button" role="radio" :aria-checked="deadline === 1" @click="deadline = 1">第一期结束</button>
            <button type="button" role="radio" :aria-checked="deadline === 2" @click="deadline = 2">允许延至第二期</button>
          </div>
        </div>
        <div class="xk-model__control">
          <span :id="`${id}-capacity`" class="xk-model__label">第二期的新增容量</span>
          <div class="xk-seg" role="radiogroup" :aria-labelledby="`${id}-capacity`">
            <button v-for="value in [0, 1, 2]" :key="value" type="button" role="radio" :aria-checked="futureCapacity === value" @click="futureCapacity = value">{{ value }} 个时段</button>
          </div>
        </div>
      </div>

      <div ref="track" class="xk-jf__track" aria-hidden="true">
        <div class="xk-jf__period">
          <div class="xk-jf__period-head"><strong>第一期</strong><span>容量 1</span></div>
          <div ref="firstBox" class="xk-jf__box"><span class="xk-jf__slot" /></div>
        </div>
        <div class="xk-jf__period">
          <div class="xk-jf__period-head"><strong>第二期</strong><span>{{ deadline === 1 ? '已经超过期限' : `容量 ${futureCapacity}` }}</span></div>
          <div ref="secondBox" class="xk-jf__box" :class="{ 'is-closed': !secondOpen || futureCapacity === 0 }">
            <template v-if="secondOpen"><span v-for="n in futureCapacity" :key="n" class="xk-jf__slot" /></template>
            <span v-if="!secondOpen || futureCapacity === 0" class="xk-jf__slot is-ghost" />
          </div>
        </div>
        <span class="xk-jf__task" :style="{ transform: placedA, opacity: ready ? 1 : 0 }">A</span>
        <span class="xk-jf__task" :class="{ 'is-blocked': !possible }" :style="{ transform: placedB, opacity: ready ? 1 : 0 }">B</span>
      </div>

      <div class="xk-jf__result" aria-live="polite">
        <strong :class="{ 'is-yes': possible }">{{ possible ? '在这些条件下，两项任务可以安排。' : '在这些条件下，不能同时按期完成。' }}</strong>
        <p>{{ deadline === 1 ? '两项任务都挤在第一期，需要 2 个时段，但容量只有 1。增加第二期容量，不能补回已经错过的期限。' : futureCapacity === 0 ? '截止时间已调整，但第二期没有新增容量，仍然缺少完成第二项任务的时段。' : '第一期完成 A，第二期完成 B。这里改变了原定期限，因此回答的是条件调整后的可行性。' }}</p>
      </div>
    </div>
    <div class="xk-model__foot">
      <p>离散教学模型；调整期限只是查看另一种条件，不代表现实中已经获得改期权限。</p>
    </div>
  </section>
</template>
