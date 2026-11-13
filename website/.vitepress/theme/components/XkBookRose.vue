<script setup lang="ts">
import { computed, ref } from 'vue'
import { useData, useRouter } from 'vitepress'
import { normalize, pageHref, shortTitle, type SidebarEntry } from '../composables/nav'

/**
 * The book as a compass rose: sixteen parts on the main ring, the four
 * appendices inside it, and the thirty-two domains of appendix D on the rim.
 * Pointing at a sector names it in the readout; a click opens that sheet. On a touch
 * screen the first tap names the sector and the second opens it.
 * The strip board below carries the same links for keyboard and screen readers.
 */
interface Sector { key: string; mark: string; label: string; title: string; href: string; d: string; at?: { x: number; y: number } }

const { theme } = useData()
const router = useRouter()

const C = 240
const point = (r: number, degrees: number) => {
  const t = (degrees * Math.PI) / 180
  return { x: C + r * Math.sin(t), y: C - r * Math.cos(t) }
}
const text = (r: number, degrees: number) => {
  const p = point(r, degrees)
  return `${p.x.toFixed(1)} ${p.y.toFixed(1)}`
}
const wedge = (inner: number, outer: number, from: number, to: number) =>
  `M${text(inner, from)} L${text(outer, from)} A${outer} ${outer} 0 0 1 ${text(outer, to)} L${text(inner, to)} A${inner} ${inner} 0 0 0 ${text(inner, from)} Z`

const entries = computed(() => {
  const groups = (theme.value.sidebar?.['/theory/'] || []) as SidebarEntry[]
  const map = new Map<string, SidebarEntry>()
  for (const entry of groups.flatMap((group) => group.items || [])) if (entry.link) map.set(normalize(entry.link), entry)
  return map
})

const sectors = computed<Sector[]>(() => {
  const list: Sector[] = []
  const add = (route: string, sector: Omit<Sector, 'title' | 'href'>) => {
    const entry = entries.value.get(route)
    if (entry) list.push({ ...sector, title: shortTitle(entry.text), href: pageHref(entry.link!) })
  }
  for (let n = 1; n <= 16; n++) {
    const from = (n - 1) * 22.5
    add(`/theory/part-${String(n).padStart(2, '0')}`, { key: `p${n}`, mark: String(n), label: `第 ${n} 部分`, d: wedge(134, 202, from, from + 22.5), at: point(168, from + 11.25) })
  }
  'abcd'.split('').forEach((letter, index) => {
    const route = entries.value.has(`/theory/appendix-${letter}/`) ? `/theory/appendix-${letter}/` : `/theory/appendix-${letter}`
    add(route, { key: `a${letter}`, mark: letter.toUpperCase(), label: `附录 ${letter.toUpperCase()}`, d: wedge(88, 134, index * 90, (index + 1) * 90), at: point(111, index * 90 + 45) })
  })
  for (let n = 1; n <= 32; n++) {
    const no = String(n).padStart(2, '0')
    const from = (n - 1) * 11.25
    add(`/theory/appendix-d/d-${no}`, { key: `d${no}`, mark: '', label: `领域 D.${no}`, d: wedge(202, 226, from + .7, from + 10.55) })
  }
  return list
})

const spokes = computed(() => {
  const lines: string[] = []
  for (let index = 0; index < 16; index++) lines.push(`M${text(134, index * 22.5)} L${text(202, index * 22.5)}`)
  for (let index = 0; index < 4; index++) lines.push(`M${text(88, index * 90)} L${text(134, index * 90)}`)
  return lines.join(' ')
})
const core = Array.from({ length: 6 }, (_, index) => text(30, index * 60)).join(' L')

const active = ref<Sector | null>(null)
const armed = ref('')
const byTouch = (event: Event) => (event as PointerEvent).pointerType === 'touch'
function enter(sector: Sector) { active.value = sector }
function leave(event: Event) { if (!byTouch(event)) active.value = null }
function open(sector: Sector, event: Event) {
  if (byTouch(event) && armed.value !== sector.key) {
    armed.value = sector.key
    active.value = sector
    return
  }
  router.go(sector.href)
}
</script>

<template>
  <div class="xk-rose" aria-hidden="true">
    <svg viewBox="0 0 480 480" focusable="false">
      <g class="xk-rose__card">
        <circle class="xk-rose__ring" :cx="C" :cy="C" r="226" />
        <circle class="xk-rose__ring" :cx="C" :cy="C" r="202" />
        <circle class="xk-rose__ring" :cx="C" :cy="C" r="134" />
        <circle class="xk-rose__ring" :cx="C" :cy="C" r="88" />
        <path class="xk-rose__spoke" :d="spokes" />
        <g v-for="sector in sectors" :key="sector.key">
          <path
            class="xk-rose__sector"
            :class="{ 'is-on': active?.key === sector.key, 'is-rim': !sector.mark }"
            :d="sector.d"
            @pointerenter="enter(sector)"
            @pointerleave="leave($event)"
            @click="open(sector, $event)"
          />
          <text v-if="sector.at" class="xk-rose__mark" :class="{ 'is-on': active?.key === sector.key }" :x="sector.at.x.toFixed(1)" :y="(sector.at.y + 6).toFixed(1)">{{ sector.mark }}</text>
        </g>
      </g>
      <path class="xk-rose__core" :d="`M${core} Z`" />
      <circle class="xk-rose__dot" :cx="C" :cy="C" r="5" />
    </svg>
    <p class="xk-rose__readout" :class="{ 'is-on': active }">
      <template v-if="active"><b>{{ active.label }}</b><span>{{ active.title }}</span></template>
      <template v-else><b>原文 XK</b><span>16 部分 · 附录 A–D · 32 领域</span></template>
    </p>
  </div>
</template>
