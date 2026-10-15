import { computed } from 'vue'
import { useData, withBase } from 'vitepress'
import { normalize, type LessonRef } from './lessonKeys'

export { bubbleLabel, lessonPath, lessonSlug, normalize, sourceRef, type LessonRef } from './lessonKeys'

export interface SidebarEntry { text: string; link?: string; items?: SidebarEntry[]; collapsed?: boolean }
export interface NavItem { text: string; link: string; route: string; no: string; title: string; lessons: number }
export interface NavGroup { text: string; items: NavItem[] }

/** A page link as a static URL: base prefix and .html, like VitePress's own links. */
export function pageHref(link: string): string {
  if (/^[a-z]+:/i.test(link)) return link
  const [path, hash] = link.split('#')
  const file = path.endsWith('/') || /\.[a-z0-9]+$/i.test(path) ? path : `${path}.html`
  return withBase(file) + (hash ? `#${hash}` : '')
}

/** VitePress relativePath → route: 'theory/part-03.md' → '/theory/part-03' */
export function routeOf(relativePath: string): string {
  return normalize('/' + relativePath)
}

/** The number a sheet carries in the book: 03, A.1, D.01, B … */
export function sheetNo(link: string): string {
  const route = normalize(link)
  let match: RegExpMatchArray | null
  if (route === '/theory/') return '00'
  if ((match = route.match(/^\/theory\/part-(\d+)$/))) return match[1]
  if ((match = route.match(/^\/theory\/appendix-a\/a-(\d+)$/))) return `A.${Number(match[1])}`
  if ((match = route.match(/^\/theory\/appendix-d\/d-(\d+)$/))) return `D.${match[1]}`
  if ((match = route.match(/^\/theory\/appendix-([a-d])\/?$/))) return match[1].toUpperCase()
  return ''
}

/** Drop the part or appendix prefix that the sheet number already shows. */
export function shortTitle(text: string): string {
  const short = text
    .replace(/^第[一二三四五六七八九十]+部分[\s\u3000]*/, '')
    .replace(/^附录[A-D][\s\u3000]*/, '')
    .replace(/^[A-D]\.\d+[\s\u3000]+/, '')
    .trim()
  return short || text
}

export function groupLabel(text: string): string {
  return text.replace(/\s*·\s*/g, ' ').trim()
}

function resolveSidebar(sidebar: unknown, route: string): SidebarEntry[] {
  if (!sidebar) return []
  if (Array.isArray(sidebar)) return sidebar as SidebarEntry[]
  const table = sidebar as Record<string, SidebarEntry[]>
  const key = Object.keys(table)
    .filter((prefix) => route.startsWith(normalize(prefix)))
    .sort((a, b) => b.length - a.length)[0]
  return key ? table[key] : []
}

/** Which pages and headings already have a lesson; the index is small and ships with the site. */
export function useLessonIndex() {
  const { theme } = useData()
  const list = computed<LessonRef[]>(() => theme.value.xkLessons || [])
  const counts = computed(() => {
    const map = new Map<string, number>()
    for (const ref of list.value) map.set(ref.route, (map.get(ref.route) || 0) + 1)
    return map
  })
  const anchors = computed(() => new Set(list.value.map((ref) => ref.anchor)))
  return { list, anchors, lessonsOn: (route: string) => counts.value.get(route) || 0 }
}

export function useNav() {
  const { theme, page } = useData()
  const { lessonsOn } = useLessonIndex()
  const route = computed(() => routeOf(page.value.relativePath))
  const toItem = (entry: SidebarEntry): NavItem => {
    const link = entry.link || '/'
    const itemRoute = normalize(link)
    return { text: entry.text, link, route: itemRoute, no: sheetNo(link), title: shortTitle(entry.text), lessons: lessonsOn(itemRoute) }
  }
  const groups = computed<NavGroup[]>(() =>
    resolveSidebar(theme.value.sidebar, route.value).map((group) => {
      const items = (group.items || []).filter((item) => item.link).map(toItem)
      // a group of mostly unnumbered pages shows no numbers at all
      if (items.filter((item) => item.no).length * 2 < items.length) items.forEach((item) => { item.no = '' })
      return { text: groupLabel(group.text), items }
    })
  )
  const flat = computed(() => groups.value.flatMap((group) => group.items))
  const index = computed(() => flat.value.findIndex((item) => item.route === route.value))
  const current = computed(() => flat.value[index.value])
  const currentGroup = computed(() => groups.value.find((group) => group.items.some((item) => item.route === route.value)))
  const prev = computed(() => (index.value > 0 ? flat.value[index.value - 1] : undefined))
  const next = computed(() => (index.value >= 0 ? flat.value[index.value + 1] : undefined))
  return { route, groups, flat, index, current, currentGroup, prev, next, lessonsOn, toItem }
}

/** Position of a route in the full reading order, used to give a page turn its direction. */
export function readingOrder(theme: any): string[] {
  const all = resolveSidebar(theme.sidebar, '/theory/')
  return all.flatMap((group) => (group.items || []).filter((item) => item.link).map((item) => normalize(item.link!)))
}
