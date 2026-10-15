<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

/**
 * The home print: twelve objects that keep re-forming into four arrangements the
 * book names — a structure object with its boundary, a chain from local to whole,
 * a feedback loop, and nested scales. A highlighted signal travels the current
 * arrangement. Static for readers who prefer reduced motion.
 */
type Point = [number, number]
interface Arrangement { label: string; ref: string; anchor: Point; leader: Point; nodes: Point[]; faint: number[]; rings: [number, number, number, number][]; path: number[] }

const ARRANGEMENTS: Arrangement[] = [
  {
    label: '结构对象', ref: '§3.1', anchor: [418, 52], leader: [392, 118],
    nodes: [[280, 236], [216, 178], [348, 172], [206, 286], [334, 304], [268, 334], [376, 240], [138, 186], [422, 288], [46, 116], [516, 352], [506, 96]],
    faint: [11],
    rings: [[280, 236, 152, .85], [280, 236, 152, 0], [280, 236, 152, 0]],
    path: [9, 7, 1, 0, 4, 6, 8, 10]
  },
  {
    label: '局部与整链', ref: '§2.4.2', anchor: [40, 70], leader: [176, 232],
    nodes: [[248, 212], [182, 252], [314, 246], [182, 372], [314, 380], [446, 372], [380, 206], [116, 214], [446, 242], [50, 258], [512, 204], [248, 96]],
    faint: [3, 4, 5, 11],
    rings: [[280, 236, 40, 0], [280, 236, 40, 0], [280, 236, 40, 0]],
    path: [9, 7, 1, 0, 2, 6, 8, 10]
  },
  {
    label: '有效反馈', ref: '§3.3', anchor: [214, 44], leader: [272, 96],
    nodes: [[414, 144], [280, 106], [470, 236], [232, 238], [328, 238], [280, 300], [414, 328], [146, 144], [280, 366], [90, 236], [146, 328], [280, 196]],
    faint: [3, 4, 5, 11],
    rings: [[280, 236, 40, 0], [280, 236, 40, 0], [280, 236, 40, 0]],
    path: [9, 7, 1, 0, 2, 6, 8, 10, 9]
  },
  {
    label: '跨尺度变换', ref: '第五部分', anchor: [392, 40], leader: [404, 104],
    nodes: [[280, 176], [155, 236], [405, 236], [232, 272], [328, 272], [280, 361], [280, 111], [101, 172], [459, 300], [186, 401], [430, 117], [374, 401]],
    faint: [],
    rings: [[280, 236, 60, .75], [280, 236, 125, .6], [280, 236, 190, .45]],
    path: [0, 6, 10]
  }
]

/* every edge that appears in any arrangement, with where it is drawn and how */
const EDGE_SETS: [number, number, string?][][] = [
  [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [3, 5], [4, 5], [2, 6], [4, 6], [1, 7], [6, 8], [7, 9], [8, 10]],
  [[9, 7], [7, 1], [1, 0], [0, 2], [2, 6], [6, 8], [8, 10], [3, 1, 'support'], [4, 2, 'support'], [5, 8, 'support']],
  [[9, 7], [7, 1], [1, 0], [0, 2], [2, 6], [6, 8, 'flow'], [8, 10, 'flow'], [10, 9, 'flow']],
  [[0, 6], [3, 1], [4, 2], [4, 5], [6, 10], [1, 7], [2, 8], [5, 9], [5, 11], [0, 3], [0, 4]]
]
const edges: { a: number; b: number; on: number[]; kind: string[] }[] = []
EDGE_SETS.forEach((set, state) => {
  for (const [x, y, kind] of set) {
    const a = Math.min(x, y)
    const b = Math.max(x, y)
    let edge = edges.find((e) => e.a === a && e.b === b)
    if (!edge) edges.push((edge = { a, b, on: [0, 0, 0, 0], kind: ['', '', '', ''] }))
    edge.on[state] = 1
    edge.kind[state] = kind || ''
  }
})

const HOLD = 4200
const MORPH = 1500
const CYCLE = HOLD + MORPH
const clock = ref(0)
const reduce = ref(false)
const root = ref<SVGSVGElement>()

const ease = (t: number) => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)
const mix = (a: number, b: number, t: number) => a + (b - a) * t

const frame = computed(() => {
  const total = clock.value % (CYCLE * ARRANGEMENTS.length)
  const index = Math.floor(total / CYCLE)
  const within = total - index * CYCLE
  const t = within < HOLD ? 0 : ease((within - HOLD) / MORPH)
  const from = ARRANGEMENTS[index]
  const to = ARRANGEMENTS[(index + 1) % ARRANGEMENTS.length]
  const toIndex = (index + 1) % ARRANGEMENTS.length
  const nodes = from.nodes.map((p, i) => ({
    x: mix(p[0], to.nodes[i][0], t),
    y: mix(p[1], to.nodes[i][1], t),
    o: mix(from.faint.includes(i) ? .35 : 1, to.faint.includes(i) ? .35 : 1, t)
  }))
  const lines = edges.map((edge) => ({
    x1: nodes[edge.a].x, y1: nodes[edge.a].y, x2: nodes[edge.b].x, y2: nodes[edge.b].y,
    o: mix(edge.on[index], edge.on[toIndex], t),
    kind: t < .5 ? edge.kind[index] : edge.kind[toIndex]
  })).filter((line) => line.o > .01)
  const rings = from.rings.map((r, i) => ({
    cx: mix(r[0], to.rings[i][0], t), cy: mix(r[1], to.rings[i][1], t), r: mix(r[2], to.rings[i][2], t), o: mix(r[3], to.rings[i][3], t)
  })).filter((ring) => ring.o > .01)
  // the signal walks the current arrangement while it holds still
  const route = from.path.map((i) => nodes[i])
  const phase = reduce.value ? .5 : Math.min(1, within / HOLD)
  const legs = route.length - 1
  const leg = Math.min(legs - 1, Math.floor(phase * legs))
  const local = phase * legs - leg
  const signal = {
    x: mix(route[leg].x, route[leg + 1].x, local),
    y: mix(route[leg].y, route[leg + 1].y, local),
    o: within < HOLD ? Math.min(1, within / 400, (HOLD - within) / 300) : 0
  }
  return { nodes, lines, rings, signal, labels: [{ a: from, o: 1 - t }, { a: to, o: t }].filter((l) => l.o > .01) }
})

let raf = 0
let last = 0
let visible = true
let observer: IntersectionObserver | undefined
let motionQuery: MediaQueryList | undefined
let startTimer = 0
let disposed = false

function tick(now: number) {
  if (disposed) return
  if (last) clock.value += Math.min(64, now - last)
  last = now
  raf = requestAnimationFrame(tick)
}
function start() {
  if (disposed || raf || reduce.value || !visible || document.hidden) return
  last = 0
  raf = requestAnimationFrame(tick)
}
function stop() {
  cancelAnimationFrame(raf)
  raf = 0
}
function onVisibility() { document.hidden ? stop() : start() }
function onMotionChange(event: MediaQueryListEvent) {
  reduce.value = event.matches
  event.matches ? stop() : start()
}

onMounted(() => {
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  reduce.value = motionQuery.matches
  motionQuery.addEventListener?.('change', onMotionChange)
  observer = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting
    visible ? start() : stop()
  })
  if (root.value) observer.observe(root.value)
  document.addEventListener('visibilitychange', onVisibility)
  startTimer = window.setTimeout(start, 1200)
})
onUnmounted(() => {
  disposed = true
  window.clearTimeout(startTimer)
  motionQuery?.removeEventListener?.('change', onMotionChange)
  stop()
  observer?.disconnect()
  document.removeEventListener('visibilitychange', onVisibility)
})
</script>

<template>
  <svg ref="root" class="xk-sf" viewBox="0 0 560 470" role="img" aria-label="结构示意：结构对象、局部与整链、有效反馈、跨尺度变换四种关系形态轮流出现">
    <g aria-hidden="true">
      <path class="xk-sf__dim" d="M14 452h532M14 444v16M546 444v16M14 452l12-4.5v9zM546 452l-12-4.5v9z" />
      <circle v-for="(ring, i) in frame.rings" :key="`r${i}`" class="xk-sf__bound" :cx="ring.cx" :cy="ring.cy" :r="ring.r" :opacity="ring.o" />
      <line
        v-for="(line, i) in frame.lines"
        :key="`l${i}`"
        class="xk-sf__edge"
        :class="{ 'is-flow': line.kind === 'flow' }"
        :x1="line.x1" :y1="line.y1" :x2="line.x2" :y2="line.y2"
        :opacity="line.kind === 'support' ? line.o * .55 : line.o"
        :stroke-dasharray="line.kind === 'support' ? '3 5' : undefined"
      />
      <circle v-for="(node, i) in frame.nodes" :key="`n${i}`" class="xk-sf__node" :cx="node.x" :cy="node.y" r="7" :opacity="node.o" />
      <circle class="xk-sf__node is-key" :cx="frame.signal.x" :cy="frame.signal.y" r="6" :opacity="frame.signal.o" />
      <circle :cx="frame.signal.x" :cy="frame.signal.y" r="14" fill="none" stroke="#ffd447" stroke-width="1" :opacity="frame.signal.o * .5" />
      <g v-for="label in frame.labels" :key="label.a.label" :opacity="label.o">
        <path class="xk-sf__label-line" :d="`M${label.a.anchor[0] + 2} ${label.a.anchor[1] + 10}L${label.a.leader[0]} ${label.a.leader[1]}`" />
        <circle :cx="label.a.leader[0]" :cy="label.a.leader[1]" r="2.5" fill="currentColor" />
        <text class="xk-sf__label" :x="label.a.anchor[0]" :y="label.a.anchor[1]">{{ label.a.label }}</text>
        <text class="xk-sf__caption" :x="label.a.anchor[0]" :y="label.a.anchor[1] + 22">{{ label.a.ref }}</text>
      </g>
    </g>
  </svg>
</template>
