<script setup lang="ts">
import { computed, ref } from 'vue'
import { useData, withBase } from 'vitepress'
import XkBookRose from './XkBookRose.vue'
import { pageHref, sheetNo, shortTitle, useLessonIndex, type SidebarEntry } from '../composables/nav'

const { theme } = useData()
const { lessonsOn } = useLessonIndex()
const query = ref('')
const groups = computed(() => (theme.value.sidebar?.['/en/theory/'] || []) as SidebarEntry[])
const cards = computed(() => theme.value.xkLessonCards || [])
const filtered = computed(() => {
  const words = query.value.trim().toLowerCase().split(/\s+/).filter(Boolean)
  return cards.value.filter((card: any) => words.every(word => `${card.key} ${card.title} ${card.lead}`.toLowerCase().includes(word)))
})
const noteLabel = (key: string) => /^(?:\d+|[A-D])(?:\.\d+)+$/.test(key) ? key : (key.startsWith('front-') ? 'Start' : 'Note')
const notePath = (card: any) => `${card.route}#lesson-${card.key.toLowerCase().replaceAll('.', '-')}`
</script>

<template>
  <section class="xk-station xk-station--en" aria-labelledby="xk-hero-title">
    <div class="xk-station__inner">
      <div class="xk-station__copy">
        <h1 id="xk-hero-title" class="xk-station__title"><span>Conditions, Structure</span><span>&amp; Transformation</span></h1>
        <p class="xk-station__sub">Objects, conditions, effects, and bounded action</p>
        <p class="xk-station__by">By Xikari. Read the complete English reference edition in the book’s original order, with selected reading notes, concept guides, and sourced cases.</p>
        <div class="xk-station__actions">
          <a class="xk-sign xk-sign--go" :href="withBase('/en/theory/')">Start reading<svg class="xk-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" /></svg></a>
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
      <div><dt>Edition</dt><dd>v2 · English reference</dd></div>
      <div><dt>Structure</dt><dd>16 parts, 4 appendices</dd></div>
      <div><dt>Reading notes</dt><dd>{{ cards.length }} units</dd></div>
    </dl>
    <section class="xk-home__sec xk-english-scope">
      <h2 class="xk-home__h">What is available in English</h2>
      <p>The complete text is available in 65 reading pages, with all 397 numbered sections aligned to Chinese v2. English reading notes cover the units listed below. The Chinese site’s longer lesson manuscripts and research attachments remain in Chinese; they are not presented as translated materials. The Chinese source governs if the two texts differ.</p>
      <p><a class="xk-link" :href="pageHref('/en/guide/')">Using the reader and comparing languages</a></p>
    </section>
    <section id="map" class="xk-home__sec" aria-labelledby="xk-h-map">
      <h2 id="xk-h-map" class="xk-home__h">The complete book</h2>
      <div class="xk-board xk-board--en">
        <div v-for="group in groups" :key="group.text" class="xk-bay">
          <h3 class="xk-bay__title">{{ group.text }}</h3>
          <ul>
            <li v-for="entry in group.items || []" :key="entry.link">
              <a v-if="entry.link" class="xk-strip" :href="pageHref(entry.link)">
                <span class="xk-strip__no">{{ sheetNo(entry.link) }}</span>
                <span class="xk-strip__title">{{ shortTitle(entry.text) }}</span>
                <span v-if="lessonsOn(entry.link)" class="xk-strip__lessons" :title="`${lessonsOn(entry.link)} reading notes`">{{ lessonsOn(entry.link) }}</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
      <p class="xk-board__note">Numbers on the right count the available English reading notes on each page.</p>
    </section>
    <section v-if="cards.length" id="lessons" class="xk-home__sec" aria-labelledby="xk-h-lessons">
      <h2 id="xk-h-lessons" class="xk-home__h">English reading notes</h2>
      <div class="xk-lesson-finder">
        <label for="xk-find-lesson">Find a section, title, or key point</label>
        <div class="xk-lesson-finder__input">
          <input id="xk-find-lesson" v-model="query" type="search" placeholder="For example: 3.3, feedback, joint feasibility" autocomplete="off" aria-controls="xk-lesson-directory">
          <button v-if="query" type="button" @click="query = ''">Clear</button>
        </div>
        <p role="status" aria-live="polite">{{ query ? `${filtered.length} matching notes` : `${cards.length} notes in reading order` }}</p>
      </div>
      <div id="xk-lesson-directory" class="xk-lessons">
        <a v-for="card in filtered" :key="card.key" :href="pageHref(notePath(card))">
          <span class="xk-bubble" aria-hidden="true"><span class="xk-bubble__top" :class="{ 'is-long': noteLabel(card.key).length > 4 }">{{ noteLabel(card.key) }}</span><span class="xk-bubble__bottom">Note</span></span>
          <span><span class="xk-lessons__title">{{ card.title }}</span><span class="xk-lessons__lead">{{ card.lead }}</span></span>
        </a>
        <p v-if="!filtered.length">No matching note. Use the search at the top to search the complete English text.</p>
      </div>
    </section>
    <section class="xk-home__sec xk-dl" aria-labelledby="xk-h-dl">
      <h2 id="xk-h-dl" class="xk-home__h">Downloads and citation</h2>
      <p>Download the English reading text, the author’s original English file, and the Chinese v2 source. Cite the author, edition, section number, and corresponding page.</p>
      <p><a class="xk-sign xk-sign--go" :href="pageHref('/en/downloads')">Download the texts</a></p>
      <div class="xk-cite"><code>Xikari, On Conditions, Structure, and Transformation, v2, §3.3. English reference edition.</code></div>
    </section>
  </div>
</template>
