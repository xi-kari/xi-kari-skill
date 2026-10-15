import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { loadLessons } from '../../../scripts/lesson_data.mjs'
import { bubbleLabel, buildLessonIndex, lessonPath } from '../composables/lessonKeys'

export interface LessonCard { key: string; label: string; title: string; lead: string; path: string }
declare const data: LessonCard[]
export { data }

/** Titles and leads of every written lesson, for the home page only. */
export default {
  watch: ['../../../content/section-lessons.json', '../../../content/lesson-overrides.json', '../../../public/source-map.json'],
  load(files: string[]): LessonCard[] {
    const read = (end: string) => JSON.parse(readFileSync(files.find((file) => file.endsWith(end))!, 'utf8'))
    const lessons = loadLessons(fileURLToPath(new URL('../../../', import.meta.url))) as Record<string, any>
    const sections = read('source-map.json').sections as Record<string, string>
    return buildLessonIndex(lessons, sections).map((ref) => ({
      key: ref.key,
      label: bubbleLabel(ref.key),
      title: String(lessons[ref.key].title || ''),
      lead: String(lessons[ref.key].lead || ''),
      path: lessonPath(ref)
    }))
  }
}
