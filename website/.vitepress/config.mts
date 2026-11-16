import { readdirSync, readFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitepress'
import type MarkdownIt from 'markdown-it'
import footnote from 'markdown-it-footnote'
import englishTheorySidebar from './en-theory-sidebar.json'
import theorySidebar from './theory-sidebar.json'
import { buildLessonIndex, isLocatorNote, sourceTitle } from './theme/composables/lessonKeys'
import { prefsHeadScript } from './theme/composables/prefs'
import { loadLessons } from '../scripts/lesson_data.mjs'

const WEBSITE = fileURLToPath(new URL('..', import.meta.url))
const SOURCE_MAP = join(WEBSITE, 'public/source-map.json')
const sourceMapPath = (locale = 'zh') => locale === 'en' ? join(WEBSITE, 'public/en/source-map.json') : SOURCE_MAP

/** Lessons are read from disk (and re-read when the file changes) so edits show up on reload. */
function lessons(locale = 'zh'): Record<string, any> {
  return loadLessons(WEBSITE, locale)
}

/** Where every written lesson sits: key, page and heading. Small enough to ship with each page. */
function lessonIndex(locale = 'zh') {
  const sections = JSON.parse(readFileSync(sourceMapPath(locale), 'utf8')).sections as Record<string, string>
  return buildLessonIndex(lessons(locale), sections)
}

function lessonSearchHtml(section: string, locale = 'zh') {
  const lesson = lessons(locale)[section]
  if (!lesson) return ''
  const escape = (value: string) => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  const fields = [lesson.lead, ...(lesson.explanation || []).filter((text: unknown) => !isLocatorNote(text)), ...(lesson.argumentSteps || []),
    ...(lesson.keyTerms || []).flatMap((item: any) => [item.term, item.text]),
    ...(lesson.sourceQuotes || []).flatMap((item: any) => [item.text, item.ref]),
    ...(lesson.distinctions || []).flatMap((item: any) => [item.leftTitle, item.leftText, item.rightTitle, item.rightText]),
    ...(lesson.caseNotes || []).flatMap((item: any) => [item.title, item.text, item.boundary]),
    ...(lesson.teachingExamples || []).flatMap((item: any) => [item.title, item.text, item.assumptions, item.boundary]),
    ...(lesson.boundaries || []), ...(lesson.questions || []),
    ...(lesson.questionAnswers || []).flatMap((item: any) => [item.question, item.answer, item.basis]),
    ...(lesson.counterexamples || []).flatMap((item: any) => [item.text, item.effect]),
    lesson.applicability?.reason, ...(lesson.openQuestions || []),
    ...(lesson.sources || []).flatMap((item: any) => [sourceTitle(item), item.locator, ...(item.claim_support || []), ...(item.limits || [])]),
    lesson.summary]
  return `<h3 id="explain-${section.toLowerCase().replaceAll('.', '-')}">${locale === 'en' ? 'Reading note: ' : '讲解：'}${escape(lesson.title)}</h3>` + fields.filter(Boolean).map(value => `<p>${escape(String(value))}</p>`).join('')
}

/** The first paragraph of 范围与阅读方式, shown on the home page exactly as written. */
function openingParagraph(locale = 'zh'): string {
  try {
    const text = readFileSync(join(WEBSITE, locale === 'en' ? 'en/theory/index.md' : 'theory/index.md'), 'utf8')
    const after = text.split(locale === 'en' ? /^## Scope and.*$/m : /^## 范围与阅读方式.*$/m)[1] || ''
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

/** The date of this handbook's selected edition, independent of skill upgrades. */
function baselineDate(locale = 'zh'): string {
  try {
    const source = JSON.parse(readFileSync(sourceMapPath(locale), 'utf8'))
    const match = String(source?.source_date || '').match(/^(\d{4})-(\d{2})-(\d{2})$/)
    return match ? `${match[1]}.${match[2]}.${match[3]}` : ''
  } catch {
    return ''
  }
}

/** Chinese characters in a text: the measure of length on the title strip and the strip board. */
function countHan(text: string): number {
  let count = 0
  for (const char of text) {
    const code = char.codePointAt(0) || 0
    if (code >= 0x3400 && code <= 0x9fff) count++
  }
  return count
}

/** Length of every sheet of the book in Chinese characters, keyed by route, for the strip board. */
function sheetLengths(locale = 'zh'): Record<string, number> {
  const lengths: Record<string, number> = {}
  const prefix = locale === 'en' ? '/en/theory/' : '/theory/'
  const root = join(WEBSITE, locale === 'en' ? 'en/theory' : 'theory')
  const walk = (directory: string) => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name)
      if (entry.isDirectory()) walk(path)
      else if (entry.name.endsWith('.md')) {
        const route = prefix + relative(root, path).replace(/\\/g, '/').replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, '')
        const text = readFileSync(path, 'utf8')
        lengths[route] = locale === 'en' ? (text.match(/\b[A-Za-z]+(?:['’-][A-Za-z]+)*\b/g) || []).length : countHan(text)
      }
    }
  }
  try { walk(root) } catch { /* the board simply shows no lengths */ }
  return lengths
}

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
    { text: '地位与作用', link: '/concepts/status-and-effects' },
    { text: '问题冻结与重开', link: '/concepts/reopening-questions' },
    { text: '四种结果', link: '/concepts/four-outcomes' },
    { text: '配置与能力', link: '/concepts/allocation-and-capability' },
    { text: '受影响位置', link: '/concepts/affected-positions' },
    { text: '全有损失的选择', link: '/concepts/choices-with-loss' },
  ] },
  { text: '真实案例', collapsed: true, items: [
    { text: '案例总览', link: '/cases/' },
    { text: '火星气候轨道器', link: '/cases/mars-climate-orbiter' },
    { text: '丰田安灯系统', link: '/cases/toyota-andon' },
    { text: '民主授权的边界', link: '/cases/democratic-authorization' },
    { text: 'GitLab：服务恢复与数据完整', link: '/cases/gitlab-recovery' },
    { text: '弗林特饮水投诉', link: '/cases/flint-water-feedback' },
    { text: '伦敦出租车学员', link: '/cases/london-taxi-learning' },
    { text: '飓风伊恩与预报锥', link: '/cases/representation-hurricane-cone' },
    { text: '大西洋慈善基金会的档案', link: '/cases/atlantic-archives-exit' },
  ] },
  { text: '继续阅读', items: [
    { text: '理论原文', link: '/theory/' },
    { text: '使用指南', link: '/guide/' },
    { text: '下载原文与技能', link: '/downloads' },
  ] },
]

const englishLabels: Record<string, string> = {
  '地位与作用': 'Status and effects', '问题冻结与重开': 'Freezing and reopening questions',
  '四种结果': 'Four distinct outcomes', '配置与能力': 'Allocation and capability',
  '受影响位置': 'Affected positions', '全有损失的选择': 'Choices with unavoidable losses',
  '开始理解': 'Start here', '阅读首页': 'Reader home', '概念图解': 'Concept guides', '概念总览': 'Concept overview',
  '反馈与学习': 'Feedback and learning', '历史与载体': 'History and carriers', '局部与整链': 'Local and whole-chain validity',
  '表示与尺度': 'Representation and scale', '联合可行性': 'Joint feasibility', '承接与责任': 'Handoff and responsibility',
  '支持与恢复': 'Support and recovery', '预测与行动': 'Prediction and action', '真实案例': 'Cases', '案例总览': 'Case overview',
  '火星气候轨道器': 'Mars Climate Orbiter', '丰田安灯系统': 'Toyota andon system', '民主授权的边界': 'Limits of democratic authorization',
  'GitLab：服务恢复与数据完整': 'GitLab: recovery and data integrity', '弗林特饮水投诉': 'Flint water complaints',
  '伦敦出租车学员': 'London taxi trainees', '飓风伊恩与预报锥': 'Hurricane Ian and the forecast cone',
  '大西洋慈善基金会的档案': 'Atlantic Philanthropies archives', '继续阅读': 'Further reading', '理论原文': 'Complete text',
  '使用指南': 'Reader guide', '下载原文与技能': 'Downloads and skill'
}
function localizedSidebar(groups: any[]): any[] {
  return groups.filter(group => !group.zhOnly).map(group => ({ ...group, text: englishLabels[group.text] || group.text,
    ...(group.link ? { link: '/en' + group.link } : {}),
    ...(group.items ? { items: localizedSidebar(group.items) } : {}) }))
}
const englishLearningSidebar = localizedSidebar(learningSidebar)
function sidebar(theory: any[], learning: any[], prefix = '') {
  return { [prefix + '/']: theory, [prefix + '/theory/']: theory,
    ...Object.fromEntries(['/concepts/', '/cases/', '/guide/', '/downloads'].map(path => [prefix + path, learning])) }
}
function pageRoutes(): string[] {
  const routes: string[] = []
  const walk = (directory: string) => {
    for (const item of readdirSync(directory, { withFileTypes: true })) {
      if (item.name.startsWith('.') || ['node_modules', 'public', 'content', 'scripts'].includes(item.name)) continue
      const path = join(directory, item.name)
      if (item.isDirectory()) walk(path)
      else if (item.name.endsWith('.md') && item.name !== 'LESSONS.md')
        routes.push('/' + relative(WEBSITE, path).replace(/\\/g, '/').replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, ''))
    }
  }
  walk(WEBSITE)
  return routes
}
const englishSearchTranslations = {
  button: { buttonText: 'Search the book', buttonAriaLabel: 'Search the book' },
  modal: { displayDetails: 'Show context', resetButtonTitle: 'Clear search', backButtonTitle: 'Close search',
    noResultsText: 'No results found. Try a concept, section number, or shorter query.',
    footer: { selectText: 'Open', navigateText: 'Navigate', closeText: 'Close' } }
}
const englishCards = lessonIndex('en').map(ref => ({ ...ref, title: lessons('en')[ref.key].title, lead: lessons('en')[ref.key].lead }))

function routeAnchors(): Record<string, string[]> {
  const routes: Record<string, string[]> = { '/': ['#map', '#lessons'], '/en/': ['#map', '#lessons'] }
  for (const locale of ['zh', 'en']) {
    const source = JSON.parse(readFileSync(sourceMapPath(locale), 'utf8'))
    const add = (href: string) => {
      const [route, anchor] = href.split('#')
      if (anchor) (routes[route] ||= []).push('#' + anchor)
    }
    for (const href of Object.values(source.sections)) add(String(href))
    for (const href of Object.values(source.parts)) add(String(href))
    for (const note of lessonIndex(locale)) {
      const slug = note.key.toLowerCase().replaceAll('.', '-')
      add(`${note.route}#lesson-${slug}`)
      add(`${note.route}#explain-${slug}`)
    }
  }
  return routes
}


export default defineConfig({
  lang: 'zh-CN',
  locales: {
    root: { label: '简体中文', lang: 'zh-CN' },
    en: { label: 'English', lang: 'en', title: 'Xikari Reader',
      head: [['meta', { property: 'og:locale', content: 'en_US' }]],
      description: 'Read On Conditions, Structure, and Transformation in English, with all 421 reading lessons, examples, questions, and source notes.',
      themeConfig: { opening: openingParagraph('en'), xkBaseline: baselineDate('en'), xkLengths: sheetLengths('en'),
        xkSections: JSON.parse(readFileSync(sourceMapPath('en'), 'utf8')).sections, xkLessons: lessonIndex('en'), xkLessonCards: englishCards, sidebar: sidebar(englishTheorySidebar, englishLearningSidebar, '/en') }
    }
  },
  title: 'Xikari 原文精读',
  description: '沿《Xikari-条件结构与转化论》的原文顺序阅读，在对应章节之后查看讲解、图示与案例。',
  base: '/xi-kari-skill/handbook/',
  srcExclude: ['public/**', 'content/**', 'LESSONS.md'],
  outDir: '../docs/handbook',
  lastUpdated: false,
  scrollOffset: { selector: '.xk-topbar', padding: 20 },
  sitemap: { hostname: 'https://xi-kari.github.io/xi-kari-skill/handbook/' },
  head: [
    ['meta', { name: 'theme-color', content: '#fbfcfe', media: '(prefers-color-scheme: light)' }],
    ['meta', { name: 'theme-color', content: '#0a1326', media: '(prefers-color-scheme: dark)' }],
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/xi-kari-skill/handbook/favicon.svg' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:locale', content: 'zh_CN' }],
    ['script', {}, prefsHeadScript],
  ],
  markdown: {
    config(md) {
      md.use(footnote)
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
    const locale = pageData.relativePath.startsWith('en/') ? 'en' : 'zh'
    if (/^(en\/)?theory\//.test(pageData.relativePath)) {
      pageData.frontmatter.xkChars = (text.match(/[\u3400-\u9fff]/g) || []).length
      pageData.frontmatter.xkWords = (text.match(/\b[A-Za-z]+(?:['’-][A-Za-z]+)*\b/g) || []).length
    }
    // each page carries only the lessons placed on it
    const keys = [...text.matchAll(/<SectionLesson section="([^"]+)"/g)].map((match) => match[1])
    if (keys.length) {
      const all = lessons(locale)
      pageData.frontmatter.xkLessons = Object.fromEntries(keys.filter((key) => all[key]).map((key) => [key, all[key]]))
    }
  },
  themeConfig: {
    xkRoutes: pageRoutes(),
    xkRouteAnchors: routeAnchors(),
    xkEnglishLessonSlugs: Object.keys(lessons('en')).map(key => key.toLowerCase().replaceAll('.', '-')),
    xkSourceAnchors: Object.fromEntries(Object.entries(JSON.parse(readFileSync(SOURCE_MAP, 'utf8')).sections).map(([key, value]) => [key.toLowerCase().replaceAll('.', '-'), '#' + String(value).split('#')[1]])),
    opening: openingParagraph(),
    xkBaseline: baselineDate(),
    xkEdition: JSON.parse(readFileSync(SOURCE_MAP, 'utf8')).theory_version,
    xkLengths: sheetLengths(),
    xkLessons: lessonIndex(),
    xkSections: JSON.parse(readFileSync(SOURCE_MAP, 'utf8')).sections,
    sidebar: { ...sidebar(theorySidebar, learningSidebar), ...sidebar(englishTheorySidebar, englishLearningSidebar, '/en') },
    search: {
      provider: 'local',
      options: {
        locales: { en: { translations: englishSearchTranslations } },
        _render(src, env, md) {
          return md.render(src.replace(/<SectionLesson section="([^"]+)"\s*\/>/g,
            (_match, section) => lessonSearchHtml(section, env.relativePath?.startsWith('en/') ? 'en' : 'zh')), env)
        },
        detailedView: true,
        miniSearch: {
          options: {
            tokenize(text) {
              if (typeof Intl.Segmenter !== 'undefined') {
                return Array.from(new Intl.Segmenter(['en', 'zh'], { granularity: 'word' }).segment(text))
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
