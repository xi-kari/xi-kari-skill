export interface TextRun { kind: 'text' | 'link' | 'code' | 'strong'; text: string; href?: string }

export function safeDestination(value: unknown): string | null {
  if (typeof value !== 'string' || !value.trim()) return null
  const target = value.trim()
  const protocolCheck = target.replace(/[\u0000-\u0020\u007f]/g, '')
  if (protocolCheck.startsWith('//') || target.includes('\\')) return null
  if (/^[a-z][a-z\d+.-]*:/i.test(protocolCheck) && !/^https?:\/\//i.test(target)) return null
  if (/[\u0000-\u001f\u007f]/.test(target)) return null
  if (/^https?:\/\//i.test(target)) {
    try { new URL(target) } catch { return null }
  }
  return target
}

export function resolveDestination(value: unknown, assetBase = '/'): string | null {
  const target = safeDestination(value)
  if (!target) return null
  if (/^https?:\/\//i.test(target) || target.startsWith('#')) return target
  try {
    const resolved = new URL(target, 'https://xikari.invalid' + assetBase)
    if (resolved.origin !== 'https://xikari.invalid') return null
    if (/^\/(theory|cases|concepts|guide|downloads)(\/|$)/.test(resolved.pathname) && !resolved.pathname.endsWith('/') && !/\.[a-z\d]+$/i.test(resolved.pathname)) resolved.pathname += '.html'
    return resolved.pathname + resolved.search + resolved.hash
  } catch {
    return null
  }
}

export function inlineRuns(value: unknown, sections: Record<string, string> = {}): TextRun[] {
  const text = typeof value === 'string' ? value : String(value ?? '')
  const runs: TextRun[] = []
  let plain = ''
  const flush = () => { if (plain) { runs.push({ kind: 'text', text: plain }); plain = '' } }
  for (let i = 0; i < text.length;) {
    if (text[i] === '§') {
      const reference = text.slice(i).match(/^§((?:\d+|[A-D])(?:\.\d+)+)/)
      if (reference && sections[reference[1]]) {
        flush()
        runs.push({ kind: 'link', text: reference[0], href: sections[reference[1]] })
        i += reference[0].length
        continue
      }
    }
    if (text[i] === '[') {
      const endLabel = text.indexOf('](', i + 1)
      if (endLabel > i + 1 && !/[\[\]\r\n]/.test(text.slice(i + 1, endLabel))) {
        let cursor = endLabel + 2, depth = 1
        for (; cursor < text.length && depth > 0; cursor++) {
          if (text[cursor] === '\\') { cursor++; continue }
          if (text[cursor] === '(') depth++
          else if (text[cursor] === ')') depth--
        }
        if (depth === 0) {
          const destination = text.slice(endLabel + 2, cursor - 1).replace(/\\([()[\]\\])/g, '$1')
          const href = safeDestination(destination)
          if (href) {
            flush()
            runs.push({ kind: 'link', text: text.slice(i + 1, endLabel), href })
            i = cursor
            continue
          }
        }
      }
    }
    const marker = text.startsWith('**', i) ? '**' : text[i] === '`' ? '`' : ''
    if (marker) {
      const end = text.indexOf(marker, i + marker.length)
      if (end > i + marker.length && !text.slice(i, end).includes('\n')) {
        flush()
        runs.push({ kind: marker === '`' ? 'code' : 'strong', text: text.slice(i + marker.length, end) })
        i = end + marker.length
        continue
      }
    }
    plain += text[i++]
  }
  flush()
  return runs
}
