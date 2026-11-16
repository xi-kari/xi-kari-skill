<script setup lang="ts">
import { useLocale } from '../../composables/locale'
const { t, isEnglish } = useLocale()
import { computed, nextTick, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import { onContentUpdated, useData, withBase } from 'vitepress'
import XkModIcon from './XkModIcon.vue'
import XkRichText from './XkRichText.vue'
import FeedbackExplorer from '../explorers/FeedbackExplorer.vue'
import JointExplorer from '../explorers/JointExplorer.vue'
import PredictionExplorer from '../explorers/PredictionExplorer.vue'
import { bubbleLabel, lessonSlug, sourceRef as refOf } from '../../composables/nav'
import { isLocatorNote, sourceTitle } from '../../composables/lessonKeys'
import { usePrefs } from '../../composables/prefs'
import { resolveDestination } from '../../composables/richText'

/**
 * One lesson, set on its own tinted field after the original section it explains.
 * Every field comes from content/section-lessons.json; the build attaches a
 * page's lessons to that page only. A module appears only when its field has
 * content. See website/LESSONS.md for the field list.
 */
const props = defineProps<{ section: string }>()

const { frontmatter } = useData()
const lesson = computed(() => frontmatter.value.xkLessons?.[props.section])
const assetBase = computed(() => lesson.value?.taskId ? `/reading-assets/${lesson.value.taskId}/` : '/')
provide('xk-lesson-assets', assetBase)
const slug = computed(() => lessonSlug(props.section))
const label = computed(() => bubbleLabel(props.section, isEnglish.value ? 'en' : 'zh'))
const sourceRef = computed(() => isEnglish.value && !/^(?:\d+|[A-D])(?:\.\d+)+$/.test(props.section) ? 'this passage' : refOf(props.section))

const MODELS: Record<string, any> = { feedback: FeedbackExplorer, joint: JointExplorer, prediction: PredictionExplorer }
const LEGACY_MODELS: Record<string, string> = { '3.3': 'feedback', 'C.12': 'joint', '4.6': 'prediction' }
const model = computed(() => {
  const name = lesson.value?.model || LEGACY_MODELS[props.section] || ''
  return Object.hasOwn(MODELS, name) ? MODELS[name] : null
})

const figures = computed(() => {
  const list: { path: string; alt: string; caption: string }[] = []
  const item = lesson.value
  if (!item) return list
  const seen = new Set<string>()
  for (const figure of item.figures || []) {
    if (figure.path && !seen.has(figure.path)) {
      list.push({ path: figure.path, alt: figure.alt || item.title || t('图示', 'Figure'), caption: figure.caption || '' })
      seen.add(figure.path)
    }
  }
  if (item.diagramPath && !seen.has(item.diagramPath)) {
    list.push({ path: item.diagramPath, alt: item.title || t('图示', 'Figure'), caption: item.diagramCaption || t('配合本节阅读的关系示意；图中成立条件与正文一起理解。', 'A relationship diagram to read alongside the conditions stated in the source.') })
  }
  return list
})
const figureNo = (i: number) => (figures.value.length > 1 ? `${t('图', 'Figure')} ${label.value}–${i + 1}` : `${t('图', 'Figure')} ${label.value}`)

const has = (value: unknown) => Array.isArray(value) ? value.length > 0 : !!value

/* A filing note at the head of the explanation (where the text was cut from) belongs with the
   other source details, not in the reading text. */
const locatorNote = computed(() => {
  const first = lesson.value?.explanation?.[0]
  return isLocatorNote(first) ? String(first) : ''
})
const paragraphs = computed<string[]>(() => {
  const list = lesson.value?.explanation || []
  return locatorNote.value ? list.slice(1) : list
})

function link(href: unknown) {
  const target = resolveDestination(href, assetBase.value)
  if (!target) return undefined
  return /^https?:\/\//i.test(target) || target.startsWith('#') ? target : withBase(target)
}

/* In source-only reading the lesson folds away; this opens just this one. */
const prefs = usePrefs()
const open = ref(false)
const folded = computed(() => prefs.sourceOnly && !open.value)
const sourceAnchor = (id: string) => `source-${slug.value}-` + Array.from(id).map(c => c.codePointAt(0)!.toString(16)).join('-')
const sourceForCase = (example: any) => (lesson.value?.sources || []).find((item: any) => item.url === example.sourceUrl)
const readingScope = (status: string) => ({ read: t('已阅读', 'Read'), partially_read: t('部分阅读', 'Partly read'), metadata_only: t('仅元数据', 'Metadata only') }[status] || status)
const sourceType = (type: string) => ({ theory_source: t('理论原文', 'Theory source'), primary: t('一手资料', 'Primary source'), secondary: t('二手资料', 'Secondary source') }[type] || type)
const identityLabel = (identity: string) => ({ constructed_boundary: t('教学反例', 'Teaching counterexample'), real_counterevidence: t('现实反证', 'Empirical counterevidence'), source_counterexample: t('来源中的反例', 'Sourced counterexample'), unresolved_boundary: t('待判定边界', 'Unresolved boundary'), hypothetical: t('假设情景', 'Hypothetical scenario') }[identity] || t('对照与边界', 'Comparison and limits'))
/* drawn like every other block: a solid tag for what a source records, a dashed one for what is constructed */
const identitySourced = (identity: string) => identity === 'real_counterevidence' || identity === 'source_counterexample'
watch(() => prefs.sourceOnly, () => { open.value = false })
let alive = false
let scrollFrame = 0
async function revealHash() {
  if (!alive || !location.hash) return
  let id: string
  try { id = decodeURIComponent(location.hash.slice(1)) } catch { return }
  const section = document.getElementById(`lesson-${slug.value}`)
  const target = document.getElementById(id)
  if (!section || !target || (section !== target && !section.contains(target))) return
  section.classList.add('is-jump-target')
  open.value = true
  let ancestor: HTMLElement | null = target
  while (ancestor && ancestor !== section) {
    if (ancestor instanceof HTMLDetailsElement) ancestor.open = true
    ancestor = ancestor.parentElement
  }
  await nextTick()
  if (!alive) return
  cancelAnimationFrame(scrollFrame)
  scrollFrame = requestAnimationFrame(() => {
    if (!alive) return
    target.scrollIntoView({ block: 'start', behavior: 'instant' })
    section.classList.remove('is-jump-target')
  })
}
onMounted(async () => { alive = true; window.addEventListener('hashchange', revealHash); await nextTick(); revealHash() })
onContentUpdated(revealHash)
onUnmounted(() => { alive = false; window.removeEventListener('hashchange', revealHash); cancelAnimationFrame(scrollFrame) })
</script>

<template>
  <section
    v-if="lesson"
    :id="`lesson-${slug}`"
    class="xk-lesson"
    :class="{ 'is-open': open }"
    :data-section="section"
    :aria-labelledby="`explain-${slug}`"
  >
    <button type="button" class="xk-lesson__peek" :aria-expanded="open" @click="open = !open">
      <span class="xk-bubble" aria-hidden="true"><span class="xk-bubble__top">{{ label }}</span><span class="xk-bubble__bottom">{{ t('讲', 'Note') }}</span></span>
      <span class="xk-lesson__peek-text">{{ open ? t('收起这段讲解', 'Collapse this note') : t(`${sourceRef} 的讲解已收起，点开查看`, `Show the note for ${sourceRef}`) }}</span>
    </button>
    <div class="xk-lesson__fold" :inert="folded || undefined" :aria-hidden="folded || undefined">
      <div>
        <div class="xk-lesson__sheet">
          <header class="xk-lesson__head">
            <span class="xk-bubble" aria-hidden="true">
              <span class="xk-bubble__top" :class="{ 'is-long': label.length > 4 }">{{ label }}</span>
              <span class="xk-bubble__bottom">{{ t('讲', 'Note') }}</span>
            </span>
            <div class="xk-lesson__heading">
              <h3 :id="`explain-${slug}`" class="xk-lesson__title">{{ t('读懂这一节', 'Understanding this section') }}</h3>
              <p v-if="lesson.title" class="xk-lesson__topic">{{ lesson.title }}</p>
            </div>
          </header>

          <p v-if="lesson.lead" class="xk-lesson__lead"><span>{{ lesson.lead }}</span></p>
          <div v-if="has(paragraphs)" class="xk-lesson__text">
            <p v-for="(paragraph, i) in paragraphs" :key="i"><XkRichText :text="paragraph" /></p>
          </div>

          <section v-if="has(lesson.keyTerms)" class="xk-mod xk-terms">
            <h4 class="xk-mod__title"><XkModIcon name="terms" />{{ t('这一节用到的词', 'Terms used here') }}</h4>
            <dl>
              <div v-for="(term, i) in lesson.keyTerms" :key="i" class="xk-terms__item">
                <dt>{{ term.term }}<a v-if="term.href" class="xk-terms__ref" :href="link(term.href)">{{ term.ref || t('原文', 'Source') }}</a></dt>
                <dd>{{ term.text }}</dd>
              </div>
            </dl>
          </section>

          <section v-if="has(lesson.sourceQuotes)" class="xk-mod xk-quotes">
            <h4 class="xk-mod__title"><XkModIcon name="quote" />{{ t('原文这样说', 'From the source') }}</h4>
            <blockquote v-for="(quote, i) in lesson.sourceQuotes" :key="i">
              <p>{{ quote.text }}</p>
              <footer v-if="quote.ref"><a v-if="quote.href" :href="link(quote.href)">{{ quote.ref }}</a><span v-else>{{ quote.ref }}</span></footer>
            </blockquote>
          </section>

          <section v-if="has(lesson.argumentSteps)" class="xk-mod">
            <h4 class="xk-mod__title"><XkModIcon name="steps" />{{ t('论证怎样展开', 'How the argument develops') }}</h4>
            <ol class="xk-steps">
              <li v-for="(step, i) in lesson.argumentSteps" :key="i">
                <span class="xk-steps__no">{{ i + 1 }}</span>
                <p><XkRichText :text="step" /></p>
              </li>
            </ol>
          </section>

          <section v-if="has(lesson.distinctions)" class="xk-mod">
            <h4 class="xk-mod__title"><XkModIcon name="split" />{{ t('把容易混淆的地方分开', 'Distinctions to keep clear') }}</h4>
            <div v-for="(pair, i) in lesson.distinctions" :key="i" class="xk-split">
              <div class="xk-split__side">
                <p class="xk-split__term">{{ pair.leftTitle }}</p>
                <p class="xk-split__text">{{ pair.leftText }}</p>
              </div>
              <div class="xk-split__seam" aria-hidden="true"><span>≠</span></div>
              <div class="xk-split__side">
                <p class="xk-split__term">{{ pair.rightTitle }}</p>
                <p class="xk-split__text">{{ pair.rightText }}</p>
              </div>
            </div>
          </section>

          <figure v-for="(figure, i) in figures" :key="figure.path" class="xk-plate">
            <button type="button" class="xk-plate__zoom" :aria-label="t(`放大${figureNo(i)}`, `Enlarge ${figureNo(i)}`)">
              <img :src="withBase(figure.path)" :alt="figure.alt" loading="lazy" decoding="async">
            </button>
            <figcaption><span class="xk-plate__no">{{ figureNo(i) }}</span>{{ figure.caption }}</figcaption>
            <details v-if="isEnglish && lesson.translationOf && figure.alt" class="xk-figure-description" open>
              <summary>English description · original figure in Chinese</summary>
              <p><XkRichText :text="figure.alt" /></p>
            </details>
          </figure>

          <section v-for="(example, i) in lesson.teachingExamples || []" :key="`t${i}`" class="xk-mod xk-scenario">
            <h4 class="xk-mod__title xk-mod__title--plain"><XkModIcon name="scenario" />{{ example.title }}<span class="xk-tag xk-tag--assumed">{{ t('教学情景', 'Teaching scenario') }}</span></h4>
            <p v-if="example.assumptions" class="xk-scenario__setup"><b>{{ t('设定', 'Assumptions') }}</b><span>{{ example.assumptions }}</span></p>
            <p><XkRichText :text="example.text" /></p>
            <p v-if="example.boundary" class="xk-note"><b>{{ t('边界', 'Boundary') }}</b><span>{{ example.boundary }}</span></p>
          </section>

          <div v-if="model" class="xk-model-slot">
            <component :is="model" />
          </div>

          <article v-for="(example, i) in lesson.caseNotes || []" :key="`c${i}`" class="xk-mod xk-case">
            <h4 class="xk-mod__title xk-mod__title--plain"><XkModIcon name="case" />{{ example.title }}<span class="xk-tag xk-tag--sourced">{{ t('真实案例', 'Documented case') }}</span></h4>
            <p><XkRichText :text="example.text" /></p>
            <p v-if="example.sourceUrl || example.sourceLabel" class="xk-case__source">
              <b>{{ t('出处', 'Source') }}</b>
              <a v-if="link(example.sourceUrl)" :href="link(example.sourceUrl)" target="_blank" rel="noreferrer">{{ example.sourceLabel || example.sourceUrl }}</a>
              <span v-else>{{ example.sourceLabel }}</span>
              <span v-if="example.sourceLocator">{{ example.sourceLocator }}</span>
              <span v-if="sourceForCase(example)?.access_status" class="xk-source-scope">{{ t('引据范围：', 'Reading scope: ') }}{{ readingScope(sourceForCase(example).access_status) }}</span>
            </p>
            <p v-if="example.boundary" class="xk-note"><b>{{ t('适用边界', 'Scope and limits') }}</b><span>{{ example.boundary }}</span></p>
            <a v-if="example.href" class="xk-case__more" :href="link(example.href)">{{ t('展开这则案例与来源', 'Read the case and sources') }}</a>
          </article>

          <section v-if="has(lesson.counterexamples)" class="xk-mod xk-counterexamples">
            <h4 class="xk-mod__title"><XkModIcon name="split" />{{ t('反例怎样改变判断', 'What counterexamples change') }}</h4>
            <article v-for="(example, i) in lesson.counterexamples" :key="i" class="xk-counterexample">
              <p><span class="xk-tag" :class="identitySourced(example.identity) ? 'xk-tag--sourced' : 'xk-tag--assumed'">{{ identityLabel(example.identity) }}</span><XkRichText :text="example.text" /></p>
              <p class="xk-note"><b>{{ t('它限制什么', 'What it limits') }}</b><span><XkRichText :text="example.effect" /></span></p>
              <p v-if="example.sourceIds?.length" class="xk-source-links"><a v-for="id in example.sourceIds" :key="id" :href="`#${sourceAnchor(id)}`">{{ sourceTitle((lesson.sources || []).find((source: any) => source.id === id)) || id }}</a></p>
            </article>
          </section>

          <section v-if="has(lesson.boundaries)" class="xk-mod xk-limit">
            <h4 class="xk-mod__title"><XkModIcon name="limit" />{{ t('这一步还不能推出什么', 'What does not follow') }}</h4>
            <ul><li v-for="(boundary, i) in lesson.boundaries" :key="i"><XkRichText :text="boundary" /></li></ul>
          </section>

          <section v-if="lesson.applicability?.reason || has(lesson.openQuestions)" class="xk-mod xk-open-questions">
            <h4 class="xk-mod__title"><XkModIcon name="terms" />{{ t('适用范围与待回答的问题', 'Scope and open questions') }}</h4>
            <p v-if="lesson.applicability?.reason"><XkRichText :text="lesson.applicability.reason" /></p>
            <ul v-if="has(lesson.openQuestions)"><li v-for="(question, i) in lesson.openQuestions" :key="i"><XkRichText :text="question" /></li></ul>
          </section>

          <section v-if="has(lesson.questions) || has(lesson.questionAnswers)" class="xk-mod xk-check">
            <h4 class="xk-mod__title"><XkModIcon name="check" />{{ t('读完后，试着辨认', 'Check your understanding') }}</h4>
            <ol v-if="has(lesson.questions)" class="xk-check__list">
              <li v-for="(question, i) in lesson.questions" :key="i">
                <span class="xk-check__no">{{ i + 1 }}</span>
                <p>{{ question }}</p>
              </li>
            </ol>
            <div v-if="has(lesson.questionAnswers)" class="xk-answers">
              <details v-for="(answer, i) in lesson.questionAnswers" :key="i" class="xk-answer">
                <summary><span>{{ answer.question }}</span><span class="xk-answer__sign" aria-hidden="true" /></summary>
                <div class="xk-answer__body">
                  <p><XkRichText :text="answer.answer" /></p>
                  <p v-if="answer.basis" class="xk-answer__basis">{{ t('依据：', 'Basis: ') }}<XkRichText :text="answer.basis" /></p>
                </div>
              </details>
            </div>
          </section>

          <section v-if="lesson.summary" class="xk-mod xk-summary">
            <h4 class="xk-mod__title"><XkModIcon name="summary" />{{ t('收束', 'Takeaway') }}</h4>
            <p><span>{{ lesson.summary }}</span></p>
          </section>

          <nav v-if="has(lesson.caseLinks)" class="xk-lesson__more" :aria-label="t('继续阅读', 'Further reading')">
            <a v-for="item in lesson.caseLinks" :key="item.href" :href="link(item.href)"><span>{{ item.title }}</span></a>
          </nav>

          <details v-if="has(lesson.sources) || lesson.lecturePath || locatorNote || lesson.editionNote" class="xk-lesson-materials">
            <summary>{{ t('原文定位、引用资料与完整解读', 'Source locations, references, and lesson materials') }}</summary>
            <div class="xk-lesson-materials__body">
              <p v-if="isEnglish && lesson.translationOf" class="xk-materials-note">This is a translation of the corresponding Chinese reading lesson. The author’s English reference text appears above. Reading-scope statements preserve the original lesson’s research record. Archived research manuscripts, source excerpts, registers, and original figures retain their Chinese language and original dates.</p>
              <p v-if="lesson.editionNote" class="xk-materials-note"><b>{{ t('版本说明：', 'Edition note: ') }}</b><XkRichText :text="lesson.editionNote" /></p>
              <p v-if="lesson.sourceHash" class="xk-original-refs">{{ t('解读所据文本 SHA-256：', 'Source text SHA-256: ') }}{{ lesson.sourceHash }}</p>
              <p v-if="has(lesson.sourceRefs)" class="xk-original-refs"><span v-for="(item, i) in lesson.sourceRefs" :key="i">{{ item.section ? `§${item.section}` : sourceRef }} · {{ t('解读所据文本第', 'Source lines') }} {{ item.startLine || item.start_line }}–{{ item.endLine || item.end_line }} {{ t('行', '') }}</span></p>
              <p v-if="locatorNote" class="xk-original-refs"><XkRichText :text="locatorNote" /></p>
              <nav class="xk-reading-downloads" :aria-label="t('本节阅读材料', 'Materials for this section')">
                <a v-if="lesson.lecturePath" :href="link(lesson.lecturePath)" download>{{ t('完整解读原稿', 'Complete lesson manuscript (Chinese)') }}</a>
                <a v-if="lesson.sourceSlicePath" :href="link(lesson.sourceSlicePath)" download>{{ t('原文对照', 'Archived source excerpt (Chinese)') }}</a>
                <a v-if="lesson.sourcesPath" :href="link(lesson.sourcesPath)" download>{{ t('来源登记', 'Original source register (Chinese)') }}</a>
                <a v-if="lesson.diagramsPath" :href="link(lesson.diagramsPath)" download>{{ t('图解材料', 'Original diagram materials (Chinese)') }}</a>
                <a v-for="file in lesson.supplementaryFiles || []" :key="file.path" :href="link(file.path)" download>{{ file.title || file.label || file.name || t('补充数据', 'Supplementary data') }}{{ isEnglish && lesson.translationOf && /teaching_(before|after)\.txt$/.test(file.path) ? ' (Chinese)' : '' }}</a>
              </nav>
              <p class="xk-materials-note">{{ t('以下资料支持本节的具体论述，实际阅读范围和适用限制在各条记录中注明。', 'These sources support the specific claims in this note. Each entry identifies the reading scope and limits.') }}</p>
              <article v-for="source in lesson.sources || []" :id="sourceAnchor(source.id)" :key="source.id" class="xk-source-entry">
                <h5><a v-if="link(source.url)" :href="link(source.url)" target="_blank" rel="noreferrer">{{ sourceTitle(source) }}</a><span v-else>{{ sourceTitle(source) }}</span></h5>
                <p class="xk-source-entry__meta"><span v-if="source.source_type">{{ sourceType(source.source_type) }}</span><span v-if="source.version_or_date">{{ source.version_or_date }}</span><span v-if="source.access_status">{{ readingScope(source.access_status) }}</span></p>
                <p v-if="source.locator"><XkRichText :text="source.locator" /></p>
                <p v-if="source.book_locator"><XkRichText :text="source.book_locator" /></p>
                <ul v-if="source.claim_support?.length"><li v-for="(support, i) in source.claim_support" :key="i"><XkRichText :text="support" /></li></ul>
                <ul v-if="source.limits?.length" class="xk-source-limits"><li v-for="(limit, i) in source.limits" :key="i"><XkRichText :text="limit" /></li></ul>
              </article>
            </div>
          </details>
        </div>
      </div>
    </div>
  </section>
</template>
