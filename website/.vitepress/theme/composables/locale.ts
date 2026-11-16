import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onContentUpdated, useData } from 'vitepress'
import { normalize } from './lessonKeys'

export function withoutLocale(path: string): string {
  return path.replace(/^\/en(?=\/|$)/, '') || '/'
}

/** Locale follows the page URL, including during client-side navigation. */
export function useLocale() {
  const { page, theme, localeIndex } = useData()
  const isEnglish = computed(() => localeIndex.value === 'en' || page.value.relativePath.startsWith('en/'))
  const t = (zh: string, en: string): string => isEnglish.value ? en : zh
  const localePath = (path: string): string => {
    if (!path.startsWith('/') || path.startsWith('//') || path.startsWith('/en/')) return path
    return isEnglish.value ? '/en' + path : path
  }
  return { isEnglish, t, localePath, theme }
}

/** Keep the reader at the corresponding section, falling back to its source when a lesson is untranslated. */
export function useLanguageSwitch() {
  const { page, theme } = useData()
  const { isEnglish } = useLocale()
  const hash = ref('')
  const sourceSection = ref('')
  const update = () => {
    hash.value = location.hash
    sourceSection.value = ''
    if (!/^#fn(?:ref)?\d/.test(hash.value)) return
    const target = document.getElementById(hash.value.slice(1))
    const backlink = target?.closest('li.footnote-item')?.querySelector<HTMLAnchorElement>('a.footnote-backref')?.hash
    const reference = backlink ? document.getElementById(backlink.slice(1)) : target
    if (!reference) return
    for (const heading of document.querySelectorAll<HTMLElement>('.xk-prose [id^="section-"], .xk-prose #reading-scope')) {
      if (heading.compareDocumentPosition(reference) & Node.DOCUMENT_POSITION_FOLLOWING) sourceSection.value = '#' + heading.id
    }
  }
  onContentUpdated(update)
  onMounted(() => { update(); window.addEventListener('hashchange', update) })
  onUnmounted(() => window.removeEventListener('hashchange', update))
  return computed(() => {
    const route = normalize('/' + page.value.relativePath)
    const target = isEnglish.value ? withoutLocale(route) : '/en' + route
    const available = new Set<string>(theme.value.xkRoutes || [])
    const destination = available.has(target) ? target : (isEnglish.value ? '/' : '/en/')
    let anchor = destination === target ? hash.value : ''
    if (!isEnglish.value && /^#(?:lesson|explain)-/.test(anchor)) {
      const slug = anchor.replace(/^#(?:lesson|explain)-/, '')
      if (!(theme.value.xkEnglishLessonSlugs || []).includes(slug)) {
        anchor = (theme.value.xkSourceAnchors || {})[slug] || ''
      }
    }
    const targetAnchors = new Set<string>(theme.value.xkRouteAnchors?.[destination] || [])
    if (anchor && !targetAnchors.has(anchor)) {
      anchor = sourceSection.value && targetAnchors.has(sourceSection.value) ? sourceSection.value : ''
    }
    return destination + anchor
  })
}
