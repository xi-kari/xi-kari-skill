import { existsSync, readFileSync, statSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { join } from 'node:path'

const cache = new Map()

/* A supplement replaces whole fields of an imported lesson, or supplies the whole lesson for a
   reading unit (content/reading-units.json) that the import lacks. */
export function loadLessons(website, locale = 'zh') {
  const content = locale === 'en' ? 'content/en' : 'content'
  const cacheKey = `${website}:${locale}`
  const source = join(website, content, 'section-lessons.json')
  const overrides = join(website, content, 'lesson-overrides.json')
  const readingUnits = join(website, content, 'reading-units.json')
  const translationManifest = join(website, content, 'translation-manifest.json')
  if (!existsSync(source)) return {}
  const translationSources = locale === 'en' ? [join(website, 'content/section-lessons.json'), join(website, 'content/lesson-overrides.json')] : []
  const signature = [source, overrides, readingUnits, translationManifest, ...translationSources].map(path => existsSync(path) ? `${statSync(path).mtimeMs}:${statSync(path).size}` : '-').join('|')
  if (cache.get(cacheKey)?.signature === signature) return cache.get(cacheKey).lessons
  const bytes = readFileSync(source)
  if (locale === 'en' && existsSync(translationManifest)) {
    const binding = JSON.parse(readFileSync(translationManifest, 'utf8'))
    for (const record of [...binding.sources, binding.translation]) {
      const current = readFileSync(join(website, record.path))
      if (createHash('sha256').update(current).digest('hex') !== record.sha256) {
        throw new Error(`The English lesson translation no longer matches its bound content: ${record.path}`)
      }
    }
  }
  const lessons = JSON.parse(bytes.toString('utf8')).lessons
  if (existsSync(overrides)) {
    const edits = JSON.parse(readFileSync(overrides, 'utf8'))
    if (edits.baseSha256 !== createHash('sha256').update(bytes).digest('hex')) {
      throw new Error('The lesson supplements do not match the imported content identity.')
    }
    const units = existsSync(readingUnits)
      ? new Set(JSON.parse(readFileSync(readingUnits, 'utf8')).units.map(unit => unit.lesson_key))
      : new Set()
    for (const [key, fields] of Object.entries(edits.lessons)) {
      if (!Object.hasOwn(lessons, key) && !units.has(key)) throw new Error(`Unknown supplemented reading unit: ${key}`)
      lessons[key] = { ...(lessons[key] || {}), ...fields }
    }
  }
  cache.set(cacheKey, { signature, lessons })
  return lessons
}
