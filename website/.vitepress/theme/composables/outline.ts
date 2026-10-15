import { onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { getScrollOffset, onContentUpdated } from 'vitepress'
import { useLessonIndex } from './nav'

export interface OutlineItem { id: string; no: string; text: string; level: 2 | 3; lesson: boolean }

function onScrollFrame(callback: () => void) {
  let frame = 0
  const run = () => { frame = 0; callback() }
  const schedule = () => { if (!frame) frame = requestAnimationFrame(run) }
  onMounted(() => {
    window.addEventListener('scroll', schedule, { passive: true })
    window.addEventListener('resize', schedule, { passive: true })
  })
  onUnmounted(() => {
    window.removeEventListener('scroll', schedule)
    window.removeEventListener('resize', schedule)
    if (frame) cancelAnimationFrame(frame)
  })
  return schedule
}

/** Headings of the current sheet (not the lessons' own headings) and the one being read. */
export function useOutline() {
  const items = shallowRef<OutlineItem[]>([])
  const active = ref('')
  const { anchors } = useLessonIndex()

  function measure() {
    const offset = getScrollOffset() + 4
    const max = document.documentElement.scrollHeight - window.innerHeight
    let current = ''
    for (const item of items.value) {
      const el = document.getElementById(item.id)
      if (!el) continue
      if (el.getBoundingClientRect().top - offset <= 0) current = item.id
      else break
    }
    if (max > 0 && window.scrollY >= max - 2 && items.value.length) current = items.value[items.value.length - 1].id
    active.value = current
  }

  function collect() {
    const root = document.querySelector('.xk-prose')
    const list: OutlineItem[] = []
    root?.querySelectorAll<HTMLElement>('h2[id], h3[id]').forEach((heading) => {
      if (heading.closest('.xk-lesson, .xk-model')) return
      const number = heading.querySelector('.xk-num__n')?.textContent?.trim() || ''
      const clone = heading.cloneNode(true) as HTMLElement
      clone.querySelectorAll('.header-anchor, .xk-num, .xk-part').forEach((node) => node.remove())
      list.push({
        id: heading.id,
        no: number,
        text: (clone.textContent || '').replace(/\s+/g, ' ').trim(),
        level: heading.tagName === 'H2' ? 2 : 3,
        lesson: anchors.value.has(heading.id)
      })
    })
    items.value = list
    measure()
  }

  onScrollFrame(measure)
  onContentUpdated(collect)
  onMounted(collect)
  return { items, active }
}

/** How far down the current page the reader is, from 0 to 1. */
export function useReadingProgress() {
  const progress = ref(0)
  const measure = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight
    progress.value = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0
  }
  onScrollFrame(measure)
  onContentUpdated(measure)
  onMounted(measure)
  return progress
}
