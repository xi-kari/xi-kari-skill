import { nextTick, type Ref } from 'vue'
import type { Router, SiteData } from 'vitepress'
import { normalize, readingOrder } from './nav'

type ViewTransition = { finished: Promise<void>; ready: Promise<void>; updateCallbackDone: Promise<void> }
type TransitionDocument = Document & { startViewTransition?: (update: () => Promise<void> | void) => ViewTransition }

export function reducedMotion(): boolean {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function canTransition(): boolean {
  return typeof document !== 'undefined' && 'startViewTransition' in document && !reducedMotion()
}

/**
 * Turn the sheet when the reader moves between pages: the old page slides out,
 * the new one slides in from the side it lies on in the book. The top bar, the
 * book index and the page outline stay where they are.
 */
export function installPageTurns(router: Router, siteData: Ref<SiteData>) {
  if (typeof document === 'undefined') return
  const doc = document as TransitionDocument
  const base = siteData.value.base
  const strip = (path: string) => normalize(path.startsWith(base) ? '/' + path.slice(base.length) : path)
  let booted = false
  let lastPath = strip(location.pathname)
  let finish: (() => void) | null = null
  let fallbackTurn = false
  const afterLoad = router.onAfterPageLoad
  const afterChange = router.onAfterRouteChange

  function direction(from: string, to: string): number {
    const order = readingOrder(siteData.value.themeConfig)
    const a = order.indexOf(from)
    const b = order.indexOf(to)
    return a >= 0 && b >= 0 && b < a ? -1 : 1
  }

  router.onAfterPageLoad = async (href: string) => {
    await afterLoad?.(href)
    const to = strip(new URL(href, location.href).pathname)
    const from = lastPath
    lastPath = to
    if (!booted || to === from) return
    document.documentElement.style.setProperty('--xk-dir', String(direction(from, to)))
    if (!canTransition() || !doc.startViewTransition) {
      fallbackTurn = !reducedMotion()
      return
    }
    document.documentElement.classList.add('xk-turning')
    await new Promise<void>((release) => {
      let released = false
      const go = () => { if (!released) { released = true; release() } }
      const transition = doc.startViewTransition!(() => {
        go()
        return new Promise<void>((done) => {
          finish = done
          window.setTimeout(done, 1500)
        })
      })
      transition.finished.finally(() => document.documentElement.classList.remove('xk-turning'))
      transition.ready.catch(go)
      window.setTimeout(go, 700)
    })
  }

  router.onAfterRouteChange = async (href: string) => {
    await afterChange?.(href)
    await nextTick()
    if (!booted) {
      booted = true
      lastPath = strip(location.pathname)
      return
    }
    if (finish) {
      const done = finish
      finish = null
      done()
    } else if (fallbackTurn) {
      fallbackTurn = false
      const sheet = document.querySelector('.xk-sheet')
      sheet?.classList.remove('is-entering')
      void (sheet as HTMLElement | null)?.offsetWidth
      sheet?.classList.add('is-entering')
      window.setTimeout(() => sheet?.classList.remove('is-entering'), 600)
    }
  }
}

/** Flip between paper and blueprint, exposing the new look from the switch outward. */
export async function flipTheme(event: MouseEvent | undefined, isDark: Ref<boolean>) {
  const doc = document as TransitionDocument
  if (!canTransition() || !doc.startViewTransition || !event) {
    isDark.value = !isDark.value
    return
  }
  const x = event.clientX || window.innerWidth - 40
  const y = event.clientY || 28
  const radius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y))
  const root = document.documentElement
  root.classList.add('xk-theme-flip')
  const transition = doc.startViewTransition(async () => {
    isDark.value = !isDark.value
    await nextTick()
  })
  try {
    await transition.ready
    root.animate(
      { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
      { duration: 620, easing: 'cubic-bezier(.3, .1, .2, 1)', pseudoElement: '::view-transition-new(root)' }
    )
    await transition.finished
  } finally {
    root.classList.remove('xk-theme-flip')
  }
}
