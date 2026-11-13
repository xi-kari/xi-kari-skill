<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useData, withBase } from 'vitepress'
import XkBookRose from './XkBookRose.vue'
import XkStructureField from './XkStructureField.vue'
import { pageHref, groupLabel, normalize, sheetNo, shortTitle, useLessonIndex, type SidebarEntry } from '../composables/nav'
import { data as cases } from '../data/cases.data'
import { data as lessonCards } from '../data/lessons.data'

const { theme } = useData()
const { lessonsOn } = useLessonIndex()

/* Cases with a relation figure get a plate; the sign under the plates leads to all of them. */
const casePlates = cases.filter((item) => item.slug)

const opening = computed<string>(() => theme.value.opening || '')
const baseline = computed<string>(() => theme.value.xkBaseline || '')

/* Appendices A and D are one strip each on the board: the strip counts the appendix's own
   sheets too, the way the lesson directory below groups them. */
function sheetsOf(route: string): string[] {
  if (!/^\/theory\/appendix-[ad]\/$/.test(route)) return [route]
  const groups = (theme.value.sidebar?.['/theory/'] || []) as SidebarEntry[]
  const all = groups.flatMap((group) => group.items || []).filter((entry) => entry.link).map((entry) => normalize(entry.link!))
  return [...new Set(all.filter((sheet) => sheet.startsWith(route)))]
}

function lengthOf(route: string): string {
  const lengths = theme.value.xkLengths || {}
  const chars = sheetsOf(route).reduce((sum, sheet) => sum + Number(lengths[sheet] || 0), 0)
  if (!chars) return ''
  return chars >= 10000 ? `${(chars / 10000).toFixed(1).replace(/\.0$/, '')} 万字` : `${Math.max(100, Math.round(chars / 100) * 100)} 字`
}

/* The book laid out as four bays of strips. */
const columns = computed(() => {
  const groups: SidebarEntry[] = (theme.value.sidebar?.['/theory/'] || []) as SidebarEntry[]
  const item = (entry: SidebarEntry) => {
    const route = normalize(entry.link || '/')
    return { link: entry.link!, no: sheetNo(entry.link!), title: shortTitle(entry.text), lessons: sheetsOf(route).reduce((sum, sheet) => sum + lessonsOn(sheet), 0), length: lengthOf(route) }
  }
  const byTitle = (text: string) => groups.find((group) => group.text === text)?.items?.filter((entry) => entry.link) || []
  const start = groups[0]?.items?.filter((entry) => entry.link) || []
  const appendix = groups
    .flatMap((group) => group.items || [])
    .filter((entry) => entry.link && /^\/theory\/(appendix-[a-d]\/?|references)$/.test(normalize(entry.link)))
  const parts = ['导读与通用结构', '人类、行动者与推演', '工具、选择与治理']
  return [
    ...parts.map((title, i) => {
      const entries = [...(i === 0 ? start : []), ...byTitle(title)].map(item)
      const numbered = entries.filter((entry) => /^\d+$/.test(entry.no) && entry.no !== '00')
      const range = numbered.length ? `第 ${Number(numbered[0].no)}—${Number(numbered[numbered.length - 1].no)} 部分` : ''
      return { title: groupLabel(title), range, items: entries }
    }),
    { title: '附录与参考', range: '附录 A—D，参考文献', items: appendix.map(item) }
  ]
})

const lessons = computed(() => lessonCards.map((card) => ({ ...card, href: withBase(card.path) })))
const lessonQuery = ref('')
const expandedGroups = reactive<Record<string, boolean>>({})
const queryTerms = computed(() => lessonQuery.value.trim().toLocaleLowerCase('zh-CN').split(/\s+/).filter(Boolean))

function lessonGroupRoute(path: string): string {
  const route = normalize(path)
  const appendix = route.match(/^\/theory\/appendix-([ad])(?:\/|$)/)
  return appendix ? `/theory/appendix-${appendix[1]}/` : route
}

const lessonGroups = computed(() => {
  const sidebar = (theme.value.sidebar?.['/theory/'] || []) as SidebarEntry[]
  const titles = new Map(sidebar.flatMap((group) => group.items || [])
    .filter((entry) => entry.link)
    .map((entry) => [normalize(entry.link!), entry.text]))
  const groups = new Map<string, { id: string; title: string; items: typeof lessons.value }>()
  for (const lesson of lessons.value) {
    const id = lessonGroupRoute(lesson.path)
    if (!groups.has(id)) groups.set(id, {
      id,
      title: id === '/theory/' ? '书前 · 范围与阅读方式' : titles.get(id) || titles.get(id.replace(/\/$/, '')) || '参考文献',
      items: []
    })
    groups.get(id)!.items.push(lesson)
  }
  return [...groups.values()].map((group, index) => ({ ...group, index }))
})

const filteredLessonGroups = computed(() => lessonGroups.value.map((group) => ({
  ...group,
  items: group.items.filter((lesson) => {
    const text = `${group.title} ${lesson.key} ${lesson.title} ${lesson.lead}`.toLocaleLowerCase('zh-CN')
    return queryTerms.value.every((term) => text.includes(term))
  })
})).filter((group) => group.items.length))
const matchingLessons = computed(() => filteredLessonGroups.value.reduce((sum, group) => sum + group.items.length, 0))
const groupIsOpen = (id: string, index: number) => queryTerms.value.length > 0 || (expandedGroups[id] ?? index === 0)
const allGroupsOpen = computed(() => lessonGroups.value.every((group) => groupIsOpen(group.id, group.index)))
function rememberGroup(event: Event, id: string) {
  if (!queryTerms.value.length) expandedGroups[id] = (event.target as HTMLDetailsElement).open
}
function toggleAllGroups() {
  const open = !allGroupsOpen.value
  for (const group of lessonGroups.value) expandedGroups[group.id] = open
}

const downloads = [
  { type: 'MD', name: '完整 Markdown 原文', desc: '适合检索、引用和交给能读文件的智能体', href: '/downloads/Xikari-条件结构与转化论.md' },
  { type: 'DOCX', name: 'Word 阅读版', desc: '适合连续阅读与打印', href: '/downloads/Xikari-条件结构与转化论.docx' }
]
</script>

<template>
  <section class="xk-station" aria-labelledby="xk-hero-title">
    <div class="xk-station__inner">
      <div class="xk-station__copy">
        <h1 id="xk-hero-title" class="xk-station__title"><span>条件结构</span><span>与转化论</span></h1>
        <p class="xk-station__sub">对象 条件 作用与有限行动</p>
        <p class="xk-station__by">Xikari 著。沿原文顺序读，每一节之后接着看讲解、图示和有出处的案例。</p>
        <div class="xk-station__actions">
          <a class="xk-sign xk-sign--go" :href="withBase('/theory/')">从开篇读起<svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" /></svg></a>
          <a class="xk-sign xk-sign--field" :href="withBase('/concepts/')">先看讲解</a>
        </div>
      </div>
      <XkBookRose class="xk-station__rose" />
    </div>
  </section>

  <div class="xk-home">
    <dl class="xk-idstrip">
      <div class="xk-idstrip__wide xk-idstrip__book"><dt>书名</dt><dd>Xikari-条件结构与转化论</dd></div>
      <div><dt>著者</dt><dd>Xikari</dd></div>
      <div v-if="baseline"><dt>正文基线</dt><dd class="xk-idstrip__num">{{ baseline }}</dd></div>
      <div><dt>结构</dt><dd>十六部分，四篇附录</dd></div>
      <div><dt>讲解</dt><dd><span class="xk-idstrip__num">{{ lessons.length }}</span> 个单元</dd></div>
    </dl>

    <section id="map" class="xk-home__sec" aria-labelledby="xk-h-map">
      <h2 id="xk-h-map" class="xk-home__h">全书十六部分与四篇附录</h2>
      <div class="xk-board">
        <div v-for="column in columns" :key="column.title" class="xk-bay">
          <h3 class="xk-bay__title">{{ column.title }}</h3>
          <p class="xk-bay__range">{{ column.range }}</p>
          <ul>
            <li v-for="entry in column.items" :key="entry.link">
              <a class="xk-strip" :href="pageHref(entry.link)">
                <span class="xk-strip__no">{{ entry.no }}</span>
                <span class="xk-strip__title">{{ entry.title }}</span>
                <span v-if="entry.length" class="xk-strip__len">{{ entry.length }}</span>
                <span v-if="entry.lessons" class="xk-strip__lessons" :title="`有 ${entry.lessons} 处讲解`">{{ entry.lessons }}</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
      <p class="xk-board__note">每条右格的数字，是这一篇已有的讲解处数。</p>
    </section>

    <section v-if="opening" class="xk-home__sec xk-home__intro" aria-labelledby="xk-h-opening">
      <h2 id="xk-h-opening" class="xk-home__h">开篇第一段</h2>
      <div class="xk-home__quote-col">
        <p class="xk-home__quote">{{ opening }}</p>
        <p class="xk-home__quote-meta">全书从“范围与阅读方式”开始。这里摘出它的第一段，其余三段在开篇页接着读。<a class="xk-link" :href="withBase('/theory/#reading-scope')">读完整个开篇</a></p>
      </div>
      <figure class="xk-home__field">
        <XkStructureField />
        <figcaption>四种关系形态轮流出现：结构对象、局部与整链、有效反馈、跨尺度变换。图为示意，定义以原文各节为准。</figcaption>
      </figure>
    </section>

    <section v-if="lessons.length" id="lessons" class="xk-home__sec" aria-labelledby="xk-h-lessons">
      <h2 id="xk-h-lessons" class="xk-home__h">逐节讲解</h2>
      <div class="xk-lesson-finder">
        <label for="xk-find-lesson">查找节号、讲解题目与要点</label>
        <div class="xk-lesson-finder__input">
          <svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
          <input id="xk-find-lesson" v-model="lessonQuery" type="search" placeholder="例如：3.3、反馈、联合可行性" aria-controls="xk-lesson-directory" autocomplete="off">
          <button v-if="lessonQuery" type="button" @click="lessonQuery = ''">清空</button>
        </div>
        <div class="xk-lesson-finder__meta">
          <p role="status" aria-live="polite">{{ queryTerms.length ? `找到 ${matchingLessons} 个讲解单元` : `共 ${lessons.length} 个讲解单元，按全书顺序排列` }}</p>
          <button v-if="!queryTerms.length" type="button" @click="toggleAllGroups">{{ allGroupsOpen ? '收起全部' : '展开全部' }}</button>
        </div>
      </div>
      <div id="xk-lesson-directory" class="xk-lesson-directory">
        <details v-for="group in filteredLessonGroups" :key="group.id" class="xk-lesson-group" :open="groupIsOpen(group.id, group.index)" @toggle="rememberGroup($event, group.id)">
          <summary><span>{{ group.title }}</span><span class="xk-lesson-group__count">{{ group.items.length }} 个单元</span><svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg></summary>
          <div class="xk-lessons">
            <a v-for="lesson in group.items" :key="lesson.key" :href="lesson.href">
              <span class="xk-bubble" aria-hidden="true"><span class="xk-bubble__top" :class="{ 'is-long': lesson.label.length > 4 }">{{ lesson.label }}</span><span class="xk-bubble__bottom">讲</span></span>
              <span>
                <span class="xk-lessons__title">{{ lesson.title }}</span>
                <span class="xk-lessons__lead">{{ lesson.lead }}</span>
              </span>
            </a>
          </div>
        </details>
        <p v-if="!filteredLessonGroups.length" class="xk-lesson-directory__empty">没有找到对应讲解。试试更短的词，或用顶部搜索查找全文。</p>
      </div>
    </section>

    <section v-if="casePlates.length" class="xk-home__sec" aria-labelledby="xk-h-cases">
      <h2 id="xk-h-cases" class="xk-home__h">在真实的事情里看见区别</h2>
      <div class="xk-cases">
        <a v-for="item in casePlates" :key="item.url" :href="withBase(item.url)">
          <figure class="xk-plate"><img :src="withBase(`/images/${item.slug}.svg`)" :alt="`${item.title}的关系图`" loading="lazy" decoding="async"></figure>
          <span class="xk-cases__text">
            <span class="xk-cases__title">{{ item.title }}</span>
            <span class="xk-tag xk-tag--sourced">{{ item.source }}</span>
          </span>
        </a>
      </div>
      <p v-if="cases.length > casePlates.length" class="xk-cases__more">
        <a class="xk-sign xk-sign--plain" :href="withBase('/cases/')">全部 {{ cases.length }} 篇案例<svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" /></svg></a>
      </p>
    </section>

    <section class="xk-home__sec xk-dl" aria-labelledby="xk-h-dl">
      <h2 id="xk-h-dl" class="xk-home__h">下载与引用</h2>
      <div class="xk-dl__files">
        <a v-for="file in downloads" :key="file.type" class="xk-file" :href="withBase(file.href)" download>
          <span class="xk-file__type" aria-hidden="true">{{ file.type }}</span>
          <span><span class="xk-file__name">{{ file.name }}</span><span class="xk-file__desc">{{ file.desc }}</span></span>
        </a>
      </div>
      <div class="xk-cite">
        <p>引用时写明作者、书名和节号，并附上对应章节的链接。</p>
        <code>Xikari，《Xikari-条件结构与转化论》，§3.3。</code>
        <p><a class="xk-link" :href="pageHref('/downloads')">文本身份与校验值</a></p>
      </div>
    </section>
  </div>
</template>
