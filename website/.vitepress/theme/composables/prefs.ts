import { reactive, watch } from 'vue'

export type TextSize = 's' | 'm' | 'l'
export type BodyFace = 'sans' | 'fang'
export interface ReadingPrefs { size: TextSize; body: BodyFace; sourceOnly: boolean }

export const PREFS_KEY = 'xk-reading'

/** Runs in <head> before the first paint so a returning reader never sees the page jump. */
export const prefsHeadScript = `;(() => { try {
  const p = JSON.parse(localStorage.getItem('${PREFS_KEY}') || '{}')
  const c = document.documentElement.classList
  if (p.size === 's') c.add('xk-size-s')
  if (p.size === 'l') c.add('xk-size-l')
  if (p.body === 'fang') c.add('xk-body-fang')
  if (p.sourceOnly) c.add('xk-source-only')
} catch (e) {} })()`

const state = reactive<ReadingPrefs>({ size: 'm', body: 'sans', sourceOnly: false })
let started = false

function apply() {
  const classes = document.documentElement.classList
  classes.toggle('xk-size-s', state.size === 's')
  classes.toggle('xk-size-l', state.size === 'l')
  classes.toggle('xk-body-fang', state.body === 'fang')
  classes.toggle('xk-source-only', state.sourceOnly)
}

/** Read saved preferences once, after hydration, and keep them in sync from then on. */
export function startPrefs() {
  if (started || typeof window === 'undefined') return
  started = true
  try {
    const saved = JSON.parse(localStorage.getItem(PREFS_KEY) || '{}')
    if (saved.size === 's' || saved.size === 'm' || saved.size === 'l') state.size = saved.size
    if (saved.body === 'sans' || saved.body === 'fang') state.body = saved.body
    state.sourceOnly = saved.sourceOnly === true
  } catch {
    /* private mode or blocked storage: keep the defaults */
  }
  apply()
  watch(state, () => {
    apply()
    try { localStorage.setItem(PREFS_KEY, JSON.stringify(state)) } catch { /* ignore */ }
  }, { deep: true })
}

export function usePrefs(): ReadingPrefs {
  return state
}
