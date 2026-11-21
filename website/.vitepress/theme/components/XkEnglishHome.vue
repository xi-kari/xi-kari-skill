<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useData, withBase } from 'vitepress'
import XkBookRose from './XkBookRose.vue'
import { bubbleLabel } from '../composables/lessonKeys'
import { normalize, pageHref, sheetNo, shortTitle, useLessonIndex, type SidebarEntry } from '../composables/nav'

const { theme } = useData()
const { lessonsOn } = useLessonIndex()
const query = ref('')
const groups = computed(() => (theme.value.sidebar?.['/en/theory/'] || []) as SidebarEntry[])
const cards = computed(() => theme.value.xkLessonCards || [])
// Keep the original four bays: three runs of parts, then the four appendices.
// The appendix strips include their child sheets, which remain in the book navigation.
const columns = computed(() => {
  const entries = groups.value.flatMap(group => group.items || []).filter(entry => entry.link)
  const item = (entry: SidebarEntry) => {
    const route = normalize(entry.link!)
    const sheets = /^\/en\/theory\/appendix-[ad]\/$/.test(route)
      ? entries.map(sheet => normalize(sheet.link!)).filter(sheet => sheet.startsWith(route))
      : [route]
    const words = sheets.reduce((sum, sheet) => sum + Number(theme.value.xkLengths?.[sheet] || 0), 0)
    return {
      link: entry.link!, no: sheetNo(entry.link!), title: shortTitle(entry.text),
      lessons: sheets.reduce((sum, sheet) => sum + lessonsOn(sheet), 0),
      length: words ? `${Math.max(100, Math.round(words / 100) * 100).toLocaleString('en')} words` : ''
    }
  }
  const runs = [
    { title: 'Introduction and structure', from: 1, to: 6 },
    { title: 'Humans and projection', from: 7, to: 12 },
    { title: 'Tools and governance', from: 13, to: 16 }
  ]
  return [
    ...runs.map(({ title, from, to }) => ({
      title, range: `Parts ${from}–${to}`,
      items: entries.filter(entry => {
        const no = sheetNo(entry.link!)
        return (from === 1 && no === '00') || (/^\d+$/.test(no) && Number(no) >= from && Number(no) <= to)
      }).map(item)
    })),
    {
      title: 'Appendices and references', range: 'Appendices A–D, references',
      items: entries.filter(entry => /^\/en\/theory\/(appendix-[a-d]\/?|references)$/.test(normalize(entry.link!))).map(item)
    }
  ]
})
const queryTerms = computed(() => query.value.trim().toLowerCase().split(/\s+/).filter(Boolean))
const expandedGroups = reactive<Record<string, boolean>>({})
const lessonGroups = computed(() => {
  const titles = new Map(groups.value.flatMap(group => group.items || [])
    .filter(entry => entry.link).map(entry => [normalize(entry.link!), entry.text]))
  const directory = new Map<string, { id: string; title: string; items: typeof cards.value }>()
  for (const card of cards.value) {
    const route = normalize(card.route)
    const appendix = route.match(/^\/en\/theory\/appendix-([ad])(?:\/|$)/)
    const id = appendix ? `/en/theory/appendix-${appendix[1]}/` : route
    if (!directory.has(id)) directory.set(id, {
      id,
      title: id === '/en/theory/' ? 'Opening · Scope and reading approach' : titles.get(id) || titles.get(id.replace(/\/$/, '')) || 'References',
      items: []
    })
    directory.get(id)!.items.push(card)
  }
  return [...directory.values()].map((group, index) => ({ ...group, index }))
})
const filteredGroups = computed(() => lessonGroups.value.map(group => ({
  ...group,
  items: group.items.filter((card: any) => queryTerms.value.every(word => `${group.title} ${card.key} ${card.title} ${card.lead}`.toLowerCase().includes(word)))
})).filter(group => group.items.length))
const matchingNotes = computed(() => filteredGroups.value.reduce((sum, group) => sum + group.items.length, 0))
const groupIsOpen = (id: string, index: number) => queryTerms.value.length > 0 || (expandedGroups[id] ?? index === 0)
const allGroupsOpen = computed(() => lessonGroups.value.every(group => groupIsOpen(group.id, group.index)))
function rememberGroup(event: Event, id: string) {
  if (!queryTerms.value.length) expandedGroups[id] = (event.target as HTMLDetailsElement).open
}
function toggleAllGroups() {
  const open = !allGroupsOpen.value
  for (const group of lessonGroups.value) expandedGroups[group.id] = open
}
const noteLabel = (key: string) => bubbleLabel(key, 'en')
const notePath = (card: any) => `${card.route}#lesson-${card.key.toLowerCase().replaceAll('.', '-')}`
</script>

<template>
  <section class="xk-station xk-station--en" aria-labelledby="xk-hero-title">
    <div class="xk-station__inner">
      <div class="xk-station__copy">
        <h1 id="xk-hero-title" class="xk-station__title"><span>Conditions, Structure</span><span>&amp; Transformation</span></h1>
        <p class="xk-station__sub">Objects, conditions, effects, and bounded action</p>
        <p class="xk-station__by">By Xikari. Read the complete English reference edition in the book’s original order, with full translations of the Chinese reading lessons, concept guides, and sourced cases.</p>
        <div class="xk-station__actions">
          <a class="xk-sign xk-sign--go" :href="withBase('/en/primer/')">Ten sentences first<svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" /></svg></a>
          <a class="xk-sign xk-sign--field" :href="withBase('/en/theory/')">Start reading</a>
          <a class="xk-sign xk-sign--field" :href="withBase('/en/concepts/')">Explore the guides</a>
        </div>
      </div>
      <XkBookRose class="xk-station__rose" />
    </div>
  </section>
  <div class="xk-home">
    <dl class="xk-idstrip">
      <div class="xk-idstrip__wide xk-idstrip__book"><dt>Book</dt><dd>On Conditions, Structure, and Transformation</dd></div>
      <div><dt>Author</dt><dd>Xikari</dd></div>
      <div><dt>Edition</dt><dd>v3.0 · English reference</dd></div>
      <div><dt>Structure</dt><dd>16 parts, 4 appendices</dd></div>
      <div><dt>Reading notes</dt><dd>{{ cards.length }} units</dd></div>
    </dl>
    <section id="map" class="xk-home__sec" aria-labelledby="xk-h-map">
      <h2 id="xk-h-map" class="xk-home__h">The complete book</h2>
      <div class="xk-board xk-board--en">
        <div v-for="column in columns" :key="column.title" class="xk-bay">
          <h3 class="xk-bay__title">{{ column.title }}</h3>
          <p class="xk-bay__range">{{ column.range }}</p>
          <ul>
            <li v-for="entry in column.items" :key="entry.link">
              <a class="xk-strip" :href="pageHref(entry.link)">
                <span class="xk-strip__no">{{ entry.no }}</span>
                <span class="xk-strip__title">{{ entry.title }}</span>
                <span v-if="entry.length" class="xk-strip__len">{{ entry.length }}</span>
                <span v-if="entry.lessons" class="xk-strip__lessons" :title="`${entry.lessons} reading notes`">{{ entry.lessons }}</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
      <p class="xk-board__note">Numbers on the right count the English reading notes covered by each strip.</p>
    </section>
    <section class="xk-home__sec xk-english-scope">
      <h2 class="xk-home__h">What is available in English</h2>
      <p>The complete text is available in 65 reading pages, with all 397 numbered sections and every paragraph aligned to the Chinese v3.0. All 421 Chinese reading lessons are translated, including explanations, argument steps, examples, questions and answers, and source notes. Original figures have English descriptions. Archived research files retain their original Chinese language and dates. The Chinese source governs if the two texts differ.</p>
      <p><a class="xk-link" :href="pageHref('/en/guide/')">Using the reader and comparing languages</a></p>
    </section>
    <section v-if="cards.length" id="lessons" class="xk-home__sec" aria-labelledby="xk-h-lessons">
      <h2 id="xk-h-lessons" class="xk-home__h">English reading notes</h2>
      <div class="xk-lesson-finder">
        <label for="xk-find-lesson">Find a section, title, or key point</label>
        <div class="xk-lesson-finder__input">
          <input id="xk-find-lesson" v-model="query" type="search" placeholder="For example: 3.3, feedback, joint feasibility" autocomplete="off" aria-controls="xk-lesson-directory">
          <button v-if="query" type="button" @click="query = ''">Clear</button>
        </div>
        <div class="xk-lesson-finder__meta">
          <p role="status" aria-live="polite">{{ queryTerms.length ? `${matchingNotes} matching notes` : `${cards.length} notes in reading order` }}</p>
          <button v-if="!queryTerms.length" type="button" @click="toggleAllGroups">{{ allGroupsOpen ? 'Collapse all' : 'Expand all' }}</button>
        </div>
      </div>
      <div id="xk-lesson-directory" class="xk-lesson-directory">
        <details v-for="group in filteredGroups" :key="group.id" class="xk-lesson-group" :open="groupIsOpen(group.id, group.index)" @toggle="rememberGroup($event, group.id)">
          <summary><span>{{ group.title }}</span><span class="xk-lesson-group__count">{{ group.items.length }} notes</span><svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg></summary>
          <div class="xk-lessons">
            <a v-for="card in group.items" :key="card.key" :href="pageHref(notePath(card))">
              <span class="xk-bubble" aria-hidden="true"><span class="xk-bubble__top" :class="{ 'is-long': noteLabel(card.key).length > 4 }">{{ noteLabel(card.key) }}</span><span class="xk-bubble__bottom">Note</span></span>
              <span><span class="xk-lessons__title">{{ card.title }}</span><span class="xk-lessons__lead">{{ card.lead }}</span></span>
            </a>
          </div>
        </details>
        <p v-if="!filteredGroups.length" class="xk-lesson-directory__empty">No matching note. Use the search at the top to search the complete English text.</p>
      </div>
    </section>
    <section class="xk-home__sec xk-dl" aria-labelledby="xk-h-dl">
      <h2 id="xk-h-dl" class="xk-home__h">Downloads and citation</h2>
      <p>Download the English reference edition, the Chinese v3.0 text it follows, and the earlier texts: the Chinese v2.1 and v2, and the author’s English translation of v2. Cite the author, edition, section number, and corresponding page.</p>
      <p><a class="xk-sign xk-sign--go" :href="pageHref('/en/downloads')">Download the texts</a></p>
      <div class="xk-cite"><code>Xikari, On Conditions, Structure, and Transformation, v3.0, §3.3. English reference edition.</code></div>
    </section>
  </div>
</template>
