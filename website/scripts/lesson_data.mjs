import { existsSync, readFileSync, statSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { join } from 'node:path'

const cache = new Map()

export function loadLessons(website) {
  const source = join(website, 'content/section-lessons.json')
  const overrides = join(website, 'content/lesson-overrides.json')
  const signature = [source, overrides].map(path => existsSync(path) ? `${statSync(path).mtimeMs}:${statSync(path).size}` : '-').join('|')
  if (cache.get(website)?.signature === signature) return cache.get(website).lessons
  const bytes = readFileSync(source)
  const lessons = JSON.parse(bytes.toString('utf8')).lessons
  if (existsSync(overrides)) {
    const edits = JSON.parse(readFileSync(overrides, 'utf8'))
    if (edits.baseSha256 !== createHash('sha256').update(bytes).digest('hex')) {
      throw new Error('The lesson supplements do not match the imported content identity.')
    }
    for (const [key, fields] of Object.entries(edits.lessons)) {
      if (!Object.hasOwn(lessons, key)) throw new Error(`Unknown supplemented reading unit: ${key}`)
      lessons[key] = { ...lessons[key], ...fields }
    }
  }
  cache.set(website, { signature, lessons })
  return lessons
}
