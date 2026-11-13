<script setup lang="ts">
import { computed } from 'vue'

/**
 * Where a sheet lies in the book, on the same compass rose the home page uses:
 * sixteen outer sectors for the parts, four inner sectors for the appendices,
 * and the centre for the opening pages and the references.
 */
const props = defineProps<{ no: string }>()

const C = 30
const polar = (r: number, degrees: number) => {
  const t = (degrees * Math.PI) / 180
  return `${(C + r * Math.sin(t)).toFixed(2)} ${(C - r * Math.cos(t)).toFixed(2)}`
}
const wedge = (inner: number, outer: number, from: number, to: number) =>
  `M${polar(inner, from)} L${polar(outer, from)} A${outer} ${outer} 0 0 1 ${polar(outer, to)} L${polar(inner, to)} A${inner} ${inner} 0 0 0 ${polar(inner, from)} Z`

const here = computed(() => {
  const part = props.no.match(/^(\d{2})$/)
  if (part && Number(part[1]) >= 1 && Number(part[1]) <= 16) {
    const index = Number(part[1]) - 1
    return wedge(17.5, 27, index * 22.5, (index + 1) * 22.5)
  }
  const appendix = props.no.match(/^([A-D])(?:\.|$)/)
  if (appendix) {
    const index = 'ABCD'.indexOf(appendix[1])
    return wedge(9.5, 17.5, index * 90, (index + 1) * 90)
  }
  return ''
})
const ticks = Array.from({ length: 16 }, (_, index) => `M${polar(17.5, index * 22.5)} L${polar(27, index * 22.5)}`).join(' ')
const quarters = Array.from({ length: 4 }, (_, index) => `M${polar(9.5, index * 90)} L${polar(17.5, index * 90)}`).join(' ')
const core = Array.from({ length: 6 }, (_, index) => polar(5.2, index * 60)).join(' L')
</script>

<template>
  <svg class="xk-pos" viewBox="0 0 60 60" aria-hidden="true" focusable="false">
    <path v-if="here" class="xk-pos__here" :d="here" />
    <circle class="xk-pos__ring" :cx="C" :cy="C" r="27" />
    <circle class="xk-pos__ring" :cx="C" :cy="C" r="17.5" />
    <circle class="xk-pos__ring" :cx="C" :cy="C" r="9.5" />
    <path class="xk-pos__tick" :d="ticks" />
    <path class="xk-pos__tick" :d="quarters" />
    <path class="xk-pos__core" :d="`M${core} Z`" />
    <circle class="xk-pos__dot" :class="{ 'is-here': !here }" :cx="C" :cy="C" :r="here ? 1.4 : 2.6" />
  </svg>
</template>
