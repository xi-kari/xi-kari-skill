import { defineConfig } from 'vitepress'
import theorySidebar from './theory-sidebar.json'
import sectionLessons from '../content/section-lessons.json'

function lessonSearchHtml(section: string) {
  const lesson = (sectionLessons.lessons as Record<string, any>)[section]
  if (!lesson) return ''
  const escape = (value: string) => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  const fields = [lesson.lead, ...(lesson.explanation || []), ...(lesson.argumentSteps || []),
    ...(lesson.distinctions || []).flatMap((item: any) => [item.leftTitle, item.leftText, item.rightTitle, item.rightText]),
    ...(lesson.caseNotes || []).flatMap((item: any) => [item.title, item.text, item.boundary]),
    ...(lesson.teachingExamples || []).flatMap((item: any) => [item.title, item.text, item.assumptions, item.boundary]),
    ...(lesson.boundaries || []), ...(lesson.questions || []),
    ...(lesson.questionAnswers || []).flatMap((item: any) => [item.question, item.answer, item.basis])]
  return `<h3 id="explain-${section.toLowerCase().replaceAll('.', '-')}">讲解：${escape(lesson.title)}</h3>` + fields.filter(Boolean).map(value => `<p>${escape(String(value))}</p>`).join('')
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
  ] },
  { text: '真实案例', collapsed: true, items: [
    { text: '案例总览', link: '/cases/' },
    { text: '火星气候轨道器', link: '/cases/mars-climate-orbiter' },
    { text: '丰田安灯系统', link: '/cases/toyota-andon' },
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
  srcExclude: ['public/**', 'content/**'],
  outDir: '../docs/handbook',
  lastUpdated: false,
  sitemap: { hostname: 'https://xi-kari.github.io/xi-kari-skill/handbook/' },
  head: [
    ['meta', { name: 'theme-color', content: '#f9fbfe' }],
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/xi-kari-skill/handbook/favicon.svg' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:locale', content: 'zh_CN' }],
  ],
  themeConfig: {
    nav: [
      { text: '全书目录', link: '/' },
      { text: '从头读起', link: '/theory/part-01' },
      { text: '术语索引', link: '/theory/appendix-b' },
      { text: '例解索引', link: '/concepts/' },
      { text: '使用指南', link: '/guide/' },
    ],
    sidebar: {
      '/': theorySidebar,
      '/theory/': theorySidebar,
      '/concepts/': learningSidebar,
      '/cases/': learningSidebar,
      '/guide/': learningSidebar,
      '/downloads': learningSidebar,
    },
    outline: { level: [2, 3], label: '本页内容' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    sidebarMenuLabel: '阅读目录',
    returnToTopLabel: '回到顶部',
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色',
    darkModeSwitchTitle: '切换到深色',
    skipToContentLabel: '跳到正文',
    socialLinks: [{ icon: 'github', link: 'https://github.com/xi-kari/xi-kari-skill' }],
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
          button: { buttonText: '搜索概念、案例、原文', buttonAriaLabel: '搜索概念、案例、原文' },
          modal: {
            displayDetails: '显示详细结果',
            resetButtonTitle: '清空搜索',
            backButtonTitle: '关闭搜索',
            noResultsText: '没有找到相关内容，请尝试其他概念或关键词。',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
          },
        },
      },
    },
  },
})
