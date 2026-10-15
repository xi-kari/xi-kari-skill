<script setup lang="ts">
import { computed } from 'vue'

/**
 * A small structure drawing generated from the sheet number, so every part of
 * the book carries its own mark: a few objects, the relations between them,
 * one boundary, one highlighted object. Same number, same drawing.
 */
const props = defineProps<{ seed: string; size?: number }>()

function random(seed: string) {
  let h = 2166136261
  for (const char of seed) {
    h ^= char.codePointAt(0)!
    h = Math.imul(h, 16777619)
  }
  return () => {
    h ^= h << 13
    h ^= h >>> 17
    h ^= h << 5
    return ((h >>> 0) % 100000) / 100000
  }
}

const drawing = computed(() => {
  const next = random(props.seed || 'xikari')
  const grid = [14, 25.3, 36.7, 48]
  const cells: [number, number][] = []
  for (const x of grid) for (const y of grid) cells.push([x, y])
  const count = 5 + Math.floor(next() * 3)
  const nodes: [number, number][] = []
  while (nodes.length < count) {
    const cell = cells.splice(Math.floor(next() * cells.length), 1)[0]
    nodes.push([cell[0] + (next() - .5) * 4, cell[1] + (next() - .5) * 4])
  }
  const edges: [number, number][] = []
  for (let i = 1; i < nodes.length; i++) {
    let best = 0
    let bestDistance = Infinity
    for (let j = 0; j < i; j++) {
      const d = Math.hypot(nodes[i][0] - nodes[j][0], nodes[i][1] - nodes[j][1]) * (0.7 + next() * 0.6)
      if (d < bestDistance) { bestDistance = d; best = j }
    }
    edges.push([best, i])
  }
  const extraA = Math.floor(next() * nodes.length)
  const extraB = (extraA + 2 + Math.floor(next() * (nodes.length - 3))) % nodes.length
  if (!edges.some(([a, b]) => (a === extraA && b === extraB) || (a === extraB && b === extraA))) edges.push([extraA, extraB])
  const inside = nodes.slice(0, 3)
  const cx = inside.reduce((s, n) => s + n[0], 0) / inside.length
  const cy = inside.reduce((s, n) => s + n[1], 0) / inside.length
  const r = Math.max(...inside.map((n) => Math.hypot(n[0] - cx, n[1] - cy))) + 7
  return {
    nodes,
    key: Math.floor(next() * nodes.length),
    edges: edges.map(([a, b]) => ({
      d: `M${nodes[a][0].toFixed(1)} ${nodes[a][1].toFixed(1)}L${nodes[b][0].toFixed(1)} ${nodes[b][1].toFixed(1)}`,
      len: Math.hypot(nodes[a][0] - nodes[b][0], nodes[a][1] - nodes[b][1]).toFixed(1)
    })),
    bound: { cx: cx.toFixed(1), cy: cy.toFixed(1), r: Math.max(8, Math.min(r, cx - 2, cy - 2, 58 - cx, 58 - cy)).toFixed(1) }
  }
})
</script>

<template>
  <svg
    :key="seed"
    class="xk-sigil is-drawing"
    viewBox="0 0 60 60"
    :width="size || 60"
    :height="size || 60"
    aria-hidden="true"
    focusable="false"
  >
    <circle class="xk-sigil__bound" :cx="drawing.bound.cx" :cy="drawing.bound.cy" :r="drawing.bound.r" />
    <path
      v-for="(edge, i) in drawing.edges"
      :key="`e${i}`"
      class="xk-sigil__edge xk-sigil__draw"
      :d="edge.d"
      :style="{ '--len': edge.len, '--i': i }"
    />
    <circle
      v-for="(node, i) in drawing.nodes"
      :key="`n${i}`"
      class="xk-sigil__node"
      :class="{ 'is-key': i === drawing.key }"
      :cx="node[0].toFixed(1)"
      :cy="node[1].toFixed(1)"
      r="3.2"
      :style="{ '--i': i }"
    />
  </svg>
</template>
