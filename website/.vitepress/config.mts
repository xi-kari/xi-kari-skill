import { readdirSync, readFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitepress'
import type MarkdownIt from 'markdown-it'
import footnote from 'markdown-it-footnote'
import englishTheorySidebar from './en-theory-sidebar.json'
import theorySidebar from './theory-sidebar.json'
import { buildLessonIndex, isLocatorNote, normalize, sourceTitle } from './theme/composables/lessonKeys'
import { prefsHeadScript } from './theme/composables/prefs'
import { loadLessons } from '../scripts/lesson_data.mjs'

const WEBSITE = fileURLToPath(new URL('..', import.meta.url))
const SOURCE_MAP = join(WEBSITE, 'public/source-map.json')
const SITE_BASE = '/xi-kari-skill/handbook/'
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

/**
 * Codes that the book names in a section heading of their own: 'D2' is 有效反馈 (§3.3).
 * Names and places are read from the reading units, which copy each heading exactly; a
 * heading that carries several codes or a range names no single code and is left out.
 */
interface SectionTerm { name: string; key: string; href: string }
const TERM_CODE = /(?<![A-Za-z0-9_-])[A-Z][A-Za-z0-9]*(?:-[A-Z0-9]+)*(?![A-Za-z0-9_])/g
const termCache = new Map<string, Map<string, SectionTerm>>()
function sectionTerms(locale = 'zh'): Map<string, SectionTerm> {
  if (!termCache.has(locale)) {
    const terms = new Map<string, SectionTerm>()
    const units = JSON.parse(readFileSync(join(WEBSITE, locale === 'en' ? 'content/en' : 'content', 'reading-units.json'), 'utf8')).units as any[]
    for (const unit of units) {
      if (!unit.section_id || !unit.website_source_route) continue
      const title = String(unit.title_exact || '').replace(/^\S+\s+/, '')
      const codes = [...title.matchAll(TERM_CODE)].map(match => match[0]).filter(code => /\d/.test(code) || /-[A-Z]/.test(code))
      if (codes.length !== 1 || /^[A-Z]+\d+-[A-Z]+\d+$/.test(codes[0]) || terms.has(codes[0])) continue
      const name = title.replace(codes[0], ' ')
        .replace(/[（(](?:完整接口卡|full interface card)[)）]/i, '')
        .replace(/^[\s|：:]+|[\s|：:]+$/g, '').replace(/\s{2,}/g, ' ')
        .replace(/(\p{Script=Han}|[、，）])\s+(?=\p{Script=Han}|（)/gu, '$1')
      if (name) terms.set(codes[0], { name, key: unit.section_id, href: unit.website_source_route })
    }
    // A table may also name a code in the first cell of a row ("| H2 行动承接与责任分型 | ..."). Where
    // several rows do, the one in the section whose heading announces that family (H1-H6) is its place.
    const places = new Map(units.filter(unit => unit.section_id && unit.website_source_route)
      .map(unit => [String(unit.website_source_route), { key: String(unit.section_id), title: String(unit.title_exact || '') }]))
    const prefix = locale === 'en' ? '/en/theory/' : '/theory/'
    const root = join(WEBSITE, locale === 'en' ? 'en/theory' : 'theory')
    const rows = new Map<string, (SectionTerm & { family: boolean })[]>()
    const walk = (directory: string) => {
      for (const entry of readdirSync(directory, { withFileTypes: true })) {
        const path = join(directory, entry.name)
        if (entry.isDirectory()) { walk(path); continue }
        if (!entry.name.endsWith('.md')) continue
        const route = prefix + relative(root, path).replace(/\\/g, '/').replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, '')
        let place: { key: string; title: string; href: string } | null = null
        for (const line of readFileSync(path, 'utf8').split(/\r?\n/)) {
          const heading = line.match(/^#{1,4}\s.*\{#(section-[a-z0-9-]+)\}\s*$/)
          if (heading) {
            const href = route + '#' + heading[1]
            place = places.has(href) ? { ...places.get(href)!, href } : null
            continue
          }
          const row = place && line.match(/^\|\s*([A-Z][A-Za-z0-9]*(?:-[A-Z0-9]+)*)\s+([^|]{2,40}?)\s*\|/)
          if (!row || !(/\d/.test(row[1]) || /-[A-Z]/.test(row[1])) || terms.has(row[1])) continue
          const stem = row[1].replace(/\d+$/, '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
          const family = new RegExp(stem + '\\d+\\s*[-—–]\\s*' + stem + '\\d+').test(place!.title)
          rows.set(row[1], [...(rows.get(row[1]) || []), { name: row[2].trim(), key: place!.key, href: place!.href, family }])
        }
      }
    }
    try { walk(root) } catch { /* headings alone still name most codes */ }
    for (const [code, found] of rows) {
      const place = found.find(item => item.family) || found[0]
      terms.set(code, { name: place.name, key: place.key, href: place.href })
    }
    termCache.set(locale, terms)
  }
  return termCache.get(locale)!
}
function termPattern(terms: Map<string, SectionTerm>): RegExp {
  const keys = [...terms.keys()].sort((a, b) => b.length - a.length).map(key => key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  return new RegExp('(?<![A-Za-z0-9_-])(?:' + keys.join('|') + ')(?![A-Za-z0-9_])', 'g')
}

/**
 * What a reader needs before the source text of a numbered section: the lesson's own lead as
 * one plain sentence, and the names of the codes the section uses, each linked to the section
 * that defines it. Both are drawn as part of the lesson, not of the source, and fold away in
 * source-only reading. The generated theory pages are not changed.
 */
const gistCache = new Map<string, Map<string, { key: string; lead: string }>>()
function sectionGistsFor(relativePath: string): Map<string, { key: string; lead: string }> {
  if (!gistCache.has(relativePath)) {
    const locale = relativePath.startsWith('en/') ? 'en' : 'zh'
    const route = normalize('/' + relativePath)
    const all = lessons(locale)
    gistCache.set(relativePath, new Map(lessonIndex(locale)
      .filter(ref => ref.route === route && ref.anchor && typeof all[ref.key]?.lead === 'string' && all[ref.key].lead.trim())
      .map(ref => [ref.anchor, { key: ref.key, lead: String(all[ref.key].lead).trim() }])))
  }
  return gistCache.get(relativePath)!
}
function sectionGists(md: MarkdownIt) {
  const escape = (value: string) => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  md.core.ruler.push('xk_section_gists', (state) => {
    const relativePath = String(state.env?.relativePath || '')
    if (state.env?.xkSearch || !/^(en\/)?theory\//.test(relativePath)) return
    const gists = sectionGistsFor(relativePath)
    if (!gists.size) return
    const english = relativePath.startsWith('en/')
    const route = normalize('/' + relativePath)
    const terms = sectionTerms(english ? 'en' : 'zh')
    const pattern = terms.size ? termPattern(terms) : null
    const hrefOf = (term: SectionTerm) => {
      const [page, anchor] = term.href.split('#')
      return escape(page === route ? '#' + anchor : SITE_BASE + page.replace(/^\//, '') + (page.endsWith('/') ? '' : '.html') + '#' + anchor)
    }
    const tokens = state.tokens
    for (let i = tokens.length - 1; i >= 2; i--) {
      if (tokens[i].type !== 'heading_close') continue
      const open = tokens[i - 2]
      const id = open?.type === 'heading_open' ? open.attrGet('id') || '' : ''
      // a part title or the book's title page carries no strip; a numbered section set as a page title does
      if (tokens[i].tag === 'h1' && !id.startsWith('section-')) continue
      const gist = gists.get(id)
      if (!gist) continue
      // the codes this section's own text uses, in the order they first appear
      const used: string[] = []
      for (let j = i + 1; pattern && j < tokens.length && tokens[j].type !== 'heading_open'; j++) {
        if (tokens[j].type !== 'inline') continue
        for (const match of tokens[j].content.matchAll(pattern)) {
          if (terms.get(match[0])!.key !== gist.key && !used.includes(match[0])) used.push(match[0])
        }
      }
      const codes = used.length
        ? `<details class="xk-gist__codes"><summary>${english ? `Codes used in this section (${used.length})` : `本节用到的代号（${used.length}）`}</summary><ul>`
          + used.map(code => `<li><a href="${hrefOf(terms.get(code)!)}"><b>${escape(code)}</b>${escape(terms.get(code)!.name)}</a></li>`).join('')
          + '</ul></details>'
        : ''
      const block = new state.Token('html_block', '', 0)
      block.content = `<div class="xk-gist"><span class="xk-gist__tag">${english ? 'In brief' : '一句话'}</span><span class="xk-gist__text">${escape(gist.lead)}</span>${codes}</div>\n`
      tokens.splice(i + 1, 0, block)
    }
  })
}

/** Wide tables scroll inside their own frame instead of widening the page. */
function tableFrames(md: MarkdownIt) {
  md.renderer.rules.table_open = (tokens, idx, options, _env, self) => '<div class="xk-table">' + self.renderToken(tokens, idx, options)
  md.renderer.rules.table_close = (tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options) + '</div>'
}

/** The text the reading units were cut from. A lesson bound to another text says so on the page. */
function sourceIdentity(locale = 'zh'): string {
  return String(JSON.parse(readFileSync(join(WEBSITE, locale === 'en' ? 'content/en' : 'content', 'reading-units.json'), 'utf8')).source_sha256 || '')
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
    { text: '十句话入门', link: '/primer/' },
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
  '开始理解': 'Start here', '阅读首页': 'Reader home', '十句话入门': 'Ten sentences', '概念图解': 'Concept guides', '概念总览': 'Concept overview',
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
    ...Object.fromEntries(['/primer/', '/concepts/', '/cases/', '/guide/', '/downloads'].map(path => [prefix + path, learning])) }
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
      themeConfig: { opening: openingParagraph('en'), xkBaseline: baselineDate('en'), xkSourceSha256: sourceIdentity('en'), xkLengths: sheetLengths('en'),
        xkSections: JSON.parse(readFileSync(sourceMapPath('en'), 'utf8')).sections, xkLessons: lessonIndex('en'), xkLessonCards: englishCards, sidebar: sidebar(englishTheorySidebar, englishLearningSidebar, '/en') }
    }
  },
  title: 'Xikari 原文精读',
  description: '沿《Xikari-条件结构与转化论》的原文顺序阅读，在对应章节之后查看讲解、图示与案例。',
  base: SITE_BASE,
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
      sectionGists(md)
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
    xkSourceSha256: sourceIdentity(),
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
          env.xkSearch = true // the lesson text below already carries each lead once
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
