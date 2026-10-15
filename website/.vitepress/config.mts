import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitepress'
import type MarkdownIt from 'markdown-it'
import theorySidebar from './theory-sidebar.json'
import { buildLessonIndex } from './theme/composables/lessonKeys'
import { loadLessons } from '../scripts/lesson_data.mjs'

const WEBSITE = fileURLToPath(new URL('..', import.meta.url))
const SOURCE_MAP = join(WEBSITE, 'public/source-map.json')

/** Lessons are read from disk (and re-read when the file changes) so edits show up on reload. */
function lessons(): Record<string, any> {
  return loadLessons(WEBSITE)
}

/** Where every written lesson sits: key, page and heading. Small enough to ship with each page. */
function lessonIndex() {
  const sections = JSON.parse(readFileSync(SOURCE_MAP, 'utf8')).sections as Record<string, string>
  return buildLessonIndex(lessons(), sections)
}

function lessonSearchHtml(section: string) {
  const lesson = lessons()[section]
  if (!lesson) return ''
  const escape = (value: string) => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  const fields = [lesson.lead, ...(lesson.explanation || []), ...(lesson.argumentSteps || []),
    ...(lesson.keyTerms || []).flatMap((item: any) => [item.term, item.text]),
    ...(lesson.sourceQuotes || []).flatMap((item: any) => [item.text, item.ref]),
    ...(lesson.distinctions || []).flatMap((item: any) => [item.leftTitle, item.leftText, item.rightTitle, item.rightText]),
    ...(lesson.caseNotes || []).flatMap((item: any) => [item.title, item.text, item.boundary]),
    ...(lesson.teachingExamples || []).flatMap((item: any) => [item.title, item.text, item.assumptions, item.boundary]),
    ...(lesson.boundaries || []), ...(lesson.questions || []),
    ...(lesson.questionAnswers || []).flatMap((item: any) => [item.question, item.answer, item.basis]),
    ...(lesson.counterexamples || []).flatMap((item: any) => [item.text, item.effect]),
    lesson.applicability?.reason, ...(lesson.openQuestions || []),
    ...(lesson.sources || []).flatMap((item: any) => [item.title, item.locator, ...(item.claim_support || []), ...(item.limits || [])]),
    lesson.summary]
  return `<h3 id="explain-${section.toLowerCase().replaceAll('.', '-')}">讲解：${escape(lesson.title)}</h3>` + fields.filter(Boolean).map(value => `<p>${escape(String(value))}</p>`).join('')
}

/** The first paragraph of 范围与阅读方式, shown on the home page exactly as written. */
function openingParagraph(): string {
  try {
    const text = readFileSync(join(WEBSITE, 'theory/index.md'), 'utf8')
    const after = text.split(/^## 范围与阅读方式.*$/m)[1] || ''
    const paragraph = after.split(/\r?\n\s*\r?\n/).map((part) => part.trim()).find(Boolean) || ''
    return paragraph
      .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&amp;/g, '&')
  } catch {
    return ''
  }
}

/**
 * Presentation-only markup for headings: the section number of “3.1　D0 结构对象”
 * and the part prefix of “第三部分　通用结构语法” get their own spans, so the
 * number can hang in the margin. The heading text itself is unchanged.
 */
function headingNumbers(md: MarkdownIt) {
  md.core.ruler.push('xk_heading_numbers', (state) => {
    const tokens = state.tokens
    for (let i = 0; i < tokens.length - 1; i++) {
      if (tokens[i].type !== 'heading_open') continue
      const inline = tokens[i + 1]
      const first = inline?.children?.[0]
      if (!inline || inline.type !== 'inline' || !first || first.type !== 'text') continue
      const section = first.content.match(/^((?:\d+|[A-D])(?:\.\d+)+)([\s\u3000]+)/)
      const part = tokens[i].tag === 'h1' ? first.content.match(/^(第[一二三四五六七八九十]+部分|附录[A-D])([\s\u3000]+)/) : null
      const match = section || part
      if (!match) continue
      const span = new state.Token('html_inline', '', 0)
      span.content = section
        ? `<span class="xk-num"><span class="xk-num__n">${match[1]}</span><span class="xk-num__gap">${match[2]}</span></span>`
        : `<span class="xk-part">${match[1]}<span class="xk-part__gap">${match[2]}</span></span>`
      first.content = first.content.slice(match[0].length)
      inline.children!.unshift(span)
    }
  })
}

/** Wide tables scroll inside their own frame instead of widening the page. */
function tableFrames(md: MarkdownIt) {
  md.renderer.rules.table_open = (tokens, idx, options, _env, self) => '<div class="xk-table">' + self.renderToken(tokens, idx, options)
  md.renderer.rules.table_close = (tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options) + '</div>'
}

const prefsScript = `;(() => { try {
  const p = JSON.parse(localStorage.getItem('xk-reading') || '{}')
  const c = document.documentElement.classList
  if (p.size === 's') c.add('xk-size-s')
  if (p.size === 'l') c.add('xk-size-l')
  if (p.body === 'fang') c.add('xk-body-fang')
  if (p.sourceOnly) c.add('xk-source-only')
} catch (e) {} })()`

const learningSidebar = [
  { text: '开始理解', items: [
    { text: '阅读首页', link: '/' },
  ] },
  { text: '概念图解', collapsed: false, items: [
    { text: '概念总览', link: '/concepts/' },
    { text: '反馈与学习', link: '/concepts/feedback' },
    { text: '历史与载体', link: '/concepts/history' },
    { text: '局部与整链', link: '/concepts/chain' },
    { text: '表示与尺度', link: '/concepts/representation' },
    { text: '联合可行性', link: '/concepts/joint-feasibility' },
    { text: '承接与责任', link: '/concepts/responsibility' },
    { text: '支持与恢复', link: '/concepts/recovery' },
    { text: '预测与行动', link: '/concepts/prediction' },
  ] },
  { text: '真实案例', collapsed: true, items: [
    { text: '案例总览', link: '/cases/' },
    { text: '火星气候轨道器', link: '/cases/mars-climate-orbiter' },
    { text: '丰田安灯系统', link: '/cases/toyota-andon' },
    { text: '民主授权的边界', link: '/cases/democratic-authorization' },
  ] },
  { text: '继续阅读', items: [
    { text: '理论原文', link: '/theory/' },
    { text: '使用指南', link: '/guide/' },
    { text: '下载原文与技能', link: '/downloads' },
  ] },
]

export default defineConfig({
  lang: 'zh-CN',
  title: 'Xikari 原文精读',
  description: '沿《Xikari-条件结构与转化论》的原文顺序阅读，在对应章节之后查看讲解、图示与案例。',
  base: '/xi-kari-skill/handbook/',
  srcExclude: ['public/**', 'content/**', 'LESSONS.md'],
  outDir: '../docs/handbook',
  lastUpdated: false,
  scrollOffset: { selector: '.xk-topbar', padding: 20 },
  sitemap: { hostname: 'https://xi-kari.github.io/xi-kari-skill/handbook/' },
  head: [
    ['meta', { name: 'theme-color', content: '#e7ebee', media: '(prefers-color-scheme: light)' }],
    ['meta', { name: 'theme-color', content: '#0a1630', media: '(prefers-color-scheme: dark)' }],
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/xi-kari-skill/handbook/favicon.svg' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:locale', content: 'zh_CN' }],
    ['script', {}, prefsScript],
  ],
  markdown: {
    config(md) {
      headingNumbers(md)
      tableFrames(md)
    },
  },
  transformPageData(pageData, { siteConfig }) {
    let text = ''
    try {
      text = readFileSync(join(siteConfig.srcDir, pageData.relativePath), 'utf8')
    } catch {
      return
    }
    if (pageData.relativePath.startsWith('theory/')) {
      pageData.frontmatter.xkChars = (text.match(/[\u3400-\u9fff]/g) || []).length
    }
    // each page carries only the lessons placed on it
    const keys = [...text.matchAll(/<SectionLesson section="([^"]+)"/g)].map((match) => match[1])
    if (keys.length) {
      const all = lessons()
      pageData.frontmatter.xkLessons = Object.fromEntries(keys.filter((key) => all[key]).map((key) => [key, all[key]]))
    }
  },
  themeConfig: {
    opening: openingParagraph(),
    xkLessons: lessonIndex(),
    sidebar: {
      '/': theorySidebar,
      '/theory/': theorySidebar,
      '/concepts/': learningSidebar,
      '/cases/': learningSidebar,
      '/guide/': learningSidebar,
      '/downloads': learningSidebar,
    },
    search: {
      provider: 'local',
      options: {
        _render(src, env, md) {
          return md.render(src.replace(/<SectionLesson section="([^"]+)"\s*\/>/g,
            (_match, section) => lessonSearchHtml(section)), env)
        },
        detailedView: true,
        miniSearch: {
          options: {
            tokenize(text) {
              if (typeof Intl.Segmenter !== 'undefined') {
                return Array.from(new Intl.Segmenter('zh', { granularity: 'word' }).segment(text))
                  .filter((segment) => segment.isWordLike)
                  .map((segment) => segment.segment)
              }
              return text.match(/[A-Za-z0-9_]+|[\u3400-\u9fff]/g) || []
            },
          },
          searchOptions: { prefix: true, fuzzy: false, combineWith: 'AND' },
        },
        translations: {
          button: { buttonText: '搜索概念与原文', buttonAriaLabel: '搜索全书' },
          modal: {
            displayDetails: '显示上下文',
            resetButtonTitle: '清空搜索',
            backButtonTitle: '关闭搜索',
            noResultsText: '没有找到相关内容。换一个概念、节号或更短的关键词试试',
            footer: { selectText: '打开', navigateText: '上下移动', closeText: '关闭' },
          },
        },
      },
    },
  },
})
