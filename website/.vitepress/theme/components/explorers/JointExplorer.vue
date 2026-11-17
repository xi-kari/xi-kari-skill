<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, useId, watch } from 'vue'
import { useLocale } from '../../composables/locale'

const { t } = useLocale()

const id = useId()
const deadline = ref(1)
const futureCapacity = ref(1)
const possible = computed(() => deadline.value === 2 && futureCapacity.value >= 1)
const secondOpen = computed(() => deadline.value === 2)

function moveRadio(event: KeyboardEvent, control: 'deadline' | 'capacity') {
  if (!['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const values = control === 'deadline' ? [1, 2] : [0, 1, 2]
  const current = control === 'deadline' ? deadline.value : futureCapacity.value
  const step = ['ArrowRight', 'ArrowDown'].includes(event.key) ? 1 : -1
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? values.length - 1
    : (values.indexOf(current) + step + values.length) % values.length
  if (control === 'deadline') deadline.value = values[next]
  else futureCapacity.value = values[next]
  ;(event.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>('[role="radio"]')[next]?.focus()
}

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
  <section class="xk-model xk-jf" :aria-label="t('联合可行性教学模型', 'Joint feasibility teaching model')">
    <div class="xk-model__head">
      <span class="xk-tag xk-tag--assumed">{{ t('教学模型', 'Teaching model') }}</span>
      <p>{{ t('原文教学设定：任务 A、B 各需 1 个时段，共享同一执行资源；第一期容量为 1。', 'Source example: tasks A and B each need one time slot and share the same execution resource. Period 1 has capacity 1.') }}</p>
    </div>
    <div class="xk-model__stage">
      <div class="xk-model__controls">
        <div class="xk-model__control">
          <span :id="`${id}-deadline`" class="xk-model__label">{{ t('两项任务的截止时间', 'Deadline for both tasks') }}</span>
          <div class="xk-seg" role="radiogroup" :aria-labelledby="`${id}-deadline`" @keydown="moveRadio($event, 'deadline')">
            <button type="button" role="radio" :aria-checked="deadline === 1" :tabindex="deadline === 1 ? 0 : -1" @click="deadline = 1">{{ t('第一期结束', 'End of period 1') }}</button>
            <button type="button" role="radio" :aria-checked="deadline === 2" :tabindex="deadline === 2 ? 0 : -1" @click="deadline = 2">{{ t('允许延至第二期', 'Allow until period 2') }}</button>
          </div>
        </div>
        <div class="xk-model__control">
          <span :id="`${id}-capacity`" class="xk-model__label">{{ t('第二期的新增容量', 'Additional capacity in period 2') }}</span>
          <div class="xk-seg" role="radiogroup" :aria-labelledby="`${id}-capacity`" @keydown="moveRadio($event, 'capacity')">
            <button v-for="value in [0, 1, 2]" :key="value" type="button" role="radio" :aria-checked="futureCapacity === value" :tabindex="futureCapacity === value ? 0 : -1" @click="futureCapacity = value">{{ t(`${value} 个时段`, `${value} time ${value === 1 ? 'slot' : 'slots'}`) }}</button>
          </div>
        </div>
      </div>

      <div ref="track" class="xk-jf__track" aria-hidden="true">
        <div class="xk-jf__period">
          <div class="xk-jf__period-head"><strong>{{ t('第一期', 'Period 1') }}</strong><span>{{ t('容量 1', 'Capacity 1') }}</span></div>
          <div ref="firstBox" class="xk-jf__box"><span class="xk-jf__slot" /></div>
        </div>
        <div class="xk-jf__period">
          <div class="xk-jf__period-head"><strong>{{ t('第二期', 'Period 2') }}</strong><span>{{ deadline === 1 ? t('已经超过期限', 'Past deadline') : t(`容量 ${futureCapacity}`, `Capacity ${futureCapacity}`) }}</span></div>
          <div ref="secondBox" class="xk-jf__box" :class="{ 'is-closed': !secondOpen || futureCapacity === 0 }">
            <template v-if="secondOpen"><span v-for="n in futureCapacity" :key="n" class="xk-jf__slot" /></template>
            <span v-if="!secondOpen || futureCapacity === 0" class="xk-jf__slot is-ghost" />
          </div>
        </div>
        <span class="xk-jf__task" :style="{ transform: placedA, opacity: ready ? 1 : 0 }">A</span>
        <span class="xk-jf__task" :class="{ 'is-blocked': !possible }" :style="{ transform: placedB, opacity: ready ? 1 : 0 }">B</span>
      </div>

      <div class="xk-jf__result" aria-live="polite">
        <strong :class="{ 'is-yes': possible }">{{ possible ? t('在这些条件下，两项任务可以安排。', 'Both tasks can be scheduled under these conditions.') : t('在这些条件下，不能同时按期完成。', 'Both tasks cannot be completed by the deadline under these conditions.') }}</strong>
        <p>{{ deadline === 1 ? t('两项任务都挤在第一期，需要 2 个时段，但容量只有 1。增加第二期容量，不能补回已经错过的期限。', 'Both tasks fall in period 1. They need two slots, but capacity is only one. Additional capacity in period 2 cannot recover a missed deadline.') : futureCapacity === 0 ? t('截止时间已调整，但第二期没有新增容量，仍然缺少完成第二项任务的时段。', 'The deadline has changed, but period 2 has no additional capacity. There is still no slot for the second task.') : t('第一期完成 A，第二期完成 B。这里改变了原定期限，因此回答的是条件调整后的可行性。', 'Complete A in period 1 and B in period 2. The original deadline has changed, so this answers the feasibility question under adjusted conditions.') }}</p>
      </div>
    </div>
    <div class="xk-model__foot">
      <p>{{ t('离散教学模型；调整期限只是查看另一种条件，不代表现实中已经获得改期权限。', 'Discrete teaching model. Changing the deadline explores another condition; it does not grant authority to reschedule a real task.') }}</p>
    </div>
  </section>
</template>
