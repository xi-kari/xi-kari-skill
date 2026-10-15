<script setup lang="ts">
import { computed, inject, type ComputedRef } from 'vue'
import { useData, withBase } from 'vitepress'
import { inlineRuns, resolveDestination } from '../../composables/richText'
const props = defineProps<{ text: unknown }>()
const { theme } = useData()
const sections = computed(() => Object.fromEntries((theme.value.xkLessons || []).map((item: any) => [item.key, `${item.route}${item.route.endsWith('/') ? '' : '.html'}#${item.anchor}`])))
const runs = computed(() => inlineRuns(props.text, sections.value))
const assetBase = inject<ComputedRef<string>>('xk-lesson-assets', computed(() => '/'))
const href = (value: unknown) => {
  const target = resolveDestination(value, assetBase.value)
  if (!target) return undefined
  return /^https?:\/\//i.test(target) || target.startsWith('#') ? target : withBase(target)
}
</script>

<template>
  <span class="xk-rich"><template v-for="(run, i) in runs" :key="i"><a v-if="run.kind === 'link' && href(run.href)" :href="href(run.href)">{{ run.text }}</a><code v-else-if="run.kind === 'code'">{{ run.text }}</code><strong v-else-if="run.kind === 'strong'">{{ run.text }}</strong><template v-else>{{ run.text }}</template></template></span>
</template>
