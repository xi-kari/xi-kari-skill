/* Pure helpers shared by the theme and its build-time data loaders (no browser or VitePress imports). */

export interface LessonRef { key: string; route: string; anchor: string }

const NUMBERED = /^(?:\d+|[A-D])(?:\.\d+)+$/

/** 'C.12' → 'c-12', used in the lesson's own ids (lesson-c-12, explain-c-12). */
export function lessonSlug(key: string): string {
  return key.toLowerCase().replaceAll('.', '-')
}

/** Text for the callout bubble: the section number, or a short mark for unnumbered units. */
export function bubbleLabel(key: string): string {
  if (NUMBERED.test(key)) return key
  const part = key.match(/^intro-(\d+)-part$/)
  if (part) return part[1]
  if (key.startsWith('front-')) return '开篇'
  return '注'
}

/** How a reader refers to the place a lesson explains. */
export function sourceRef(key: string): string {
  return NUMBERED.test(key) ? `§${key}` : '本段原文'
}

/** Link (without base) to a lesson on its page: '/theory/part-03.html#lesson-3-3'. */
export function lessonPath(ref: LessonRef): string {
  return `${ref.route}${ref.route.endsWith('/') ? '' : '.html'}#lesson-${lessonSlug(ref.key)}`
}

/** '/theory/part-03.html#x' → '/theory/part-03', '/theory/index' → '/theory/' */
export function normalize(path: string): string {
  let value = path.replace(/[?#].*$/, '').replace(/\.(html|md)$/, '').replace(/(^|\/)index$/, '$1')
  if (!value.startsWith('/')) value = '/' + value
  return value
}

/** Lesson references in reading order, built from the source map and the lesson file. */
export function buildLessonIndex(
  lessons: Record<string, unknown>,
  sections: Record<string, string>,
  order: string[] = Object.keys(sections)
): LessonRef[] {
  return order
    .filter((key) => lessons[key] && sections[key])
    .map((key) => ({ key, route: normalize(sections[key]), anchor: sections[key].split('#')[1] || '' }))
}
