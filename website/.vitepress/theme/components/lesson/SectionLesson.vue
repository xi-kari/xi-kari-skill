<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import { onContentUpdated, useData, withBase } from 'vitepress'
import XkModIcon from './XkModIcon.vue'
import XkRichText from './XkRichText.vue'
import FeedbackExplorer from '../explorers/FeedbackExplorer.vue'
import JointExplorer from '../explorers/JointExplorer.vue'
import PredictionExplorer from '../explorers/PredictionExplorer.vue'
import { bubbleLabel, lessonSlug, sourceRef as refOf } from '../../composables/nav'
import { usePrefs } from '../../composables/prefs'
import { resolveDestination } from '../../composables/richText'

/**
 * One lesson, drawn on tracing paper after the original section it explains.
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
const label = computed(() => bubbleLabel(props.section))
const sourceRef = computed(() => refOf(props.section))

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
      list.push({ path: figure.path, alt: figure.alt || item.title || '图示', caption: figure.caption || '' })
      seen.add(figure.path)
    }
  }
  if (item.diagramPath && !seen.has(item.diagramPath)) {
    list.push({ path: item.diagramPath, alt: item.title || '图示', caption: item.diagramCaption || '配合本节阅读的关系示意；图中成立条件与正文一起理解。' })
  }
  return list
})
const figureNo = (i: number) => (figures.value.length > 1 ? `图 ${label.value}–${i + 1}` : `图 ${label.value}`)

const has = (value: unknown) => Array.isArray(value) ? value.length > 0 : !!value

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
const readingScope = (status: string) => ({ read: '已阅读', partially_read: '部分阅读', metadata_only: '仅元数据' }[status] || status)
const sourceType = (type: string) => ({ theory_source: '理论原文', primary: '一手资料', secondary: '二手资料' }[type] || type)
const identityLabel = (identity: string) => ({ constructed_boundary: '教学反例', real_counterevidence: '现实反证', source_counterexample: '来源中的反例', unresolved_boundary: '待判定边界', hypothetical: '假设情景' }[identity] || '对照与边界')
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
      <span class="xk-bubble" aria-hidden="true"><span class="xk-bubble__top">{{ label }}</span><span class="xk-bubble__bottom">讲</span></span>
      <span class="xk-lesson__peek-text">{{ open ? '收起这段讲解' : `${sourceRef} 的讲解已收起，点开查看` }}</span>
    </button>
    <div class="xk-lesson__fold" :inert="folded || undefined" :aria-hidden="folded || undefined">
      <div>
        <div class="xk-lesson__sheet">
          <header class="xk-lesson__head">
            <span class="xk-bubble" aria-hidden="true">
              <span class="xk-bubble__top" :class="{ 'is-long': label.length > 4 }">{{ label }}</span>
              <span class="xk-bubble__bottom">讲</span>
            </span>
            <div class="xk-lesson__heading">
              <h3 :id="`explain-${slug}`" class="xk-lesson__title">读懂这一节</h3>
              <p v-if="lesson.title" class="xk-lesson__topic">{{ lesson.title }}</p>
            </div>
          </header>

          <p v-if="lesson.lead" class="xk-lesson__lead"><span>{{ lesson.lead }}</span></p>
          <div v-if="has(lesson.explanation)" class="xk-lesson__text">
            <p v-for="(paragraph, i) in lesson.explanation" :key="i"><XkRichText :text="paragraph" /></p>
          </div>

          <section v-if="has(lesson.keyTerms)" class="xk-mod xk-terms">
            <h4 class="xk-mod__title"><XkModIcon name="terms" />这一节用到的词</h4>
            <dl>
              <div v-for="(term, i) in lesson.keyTerms" :key="i" class="xk-terms__item">
                <dt>{{ term.term }}<a v-if="term.href" class="xk-terms__ref" :href="link(term.href)">{{ term.ref || '原文' }}</a></dt>
                <dd>{{ term.text }}</dd>
              </div>
            </dl>
          </section>

          <section v-if="has(lesson.sourceQuotes)" class="xk-mod xk-quotes">
            <h4 class="xk-mod__title"><XkModIcon name="quote" />原文这样说</h4>
            <blockquote v-for="(quote, i) in lesson.sourceQuotes" :key="i">
              <p>{{ quote.text }}</p>
              <footer v-if="quote.ref"><a v-if="quote.href" :href="link(quote.href)">{{ quote.ref }}</a><span v-else>{{ quote.ref }}</span></footer>
            </blockquote>
          </section>

          <section v-if="has(lesson.argumentSteps)" class="xk-mod">
            <h4 class="xk-mod__title"><XkModIcon name="steps" />论证怎样展开</h4>
            <ol class="xk-steps">
              <li v-for="(step, i) in lesson.argumentSteps" :key="i">
                <span class="xk-steps__no">{{ i + 1 }}</span>
                <p><XkRichText :text="step" /></p>
              </li>
            </ol>
          </section>

          <section v-if="has(lesson.distinctions)" class="xk-mod">
            <h4 class="xk-mod__title"><XkModIcon name="split" />把容易混淆的地方分开</h4>
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
            <button type="button" class="xk-plate__zoom" :aria-label="`放大${figureNo(i)}`">
              <img :src="withBase(figure.path)" :alt="figure.alt" loading="lazy" decoding="async">
            </button>
            <figcaption><span class="xk-plate__no">{{ figureNo(i) }}</span>{{ figure.caption }}</figcaption>
          </figure>

          <section v-for="(example, i) in lesson.teachingExamples || []" :key="`t${i}`" class="xk-mod xk-scenario">
            <h4 class="xk-mod__title"><XkModIcon name="scenario" />{{ example.title }}<span class="xk-tag xk-tag--assumed">教学情景</span></h4>
            <p v-if="example.assumptions" class="xk-scenario__setup"><b>设定</b><span>{{ example.assumptions }}</span></p>
            <p><XkRichText :text="example.text" /></p>
            <p v-if="example.boundary" class="xk-note"><b>边界</b><span>{{ example.boundary }}</span></p>
          </section>

          <div v-if="model" class="xk-model-slot">
            <component :is="model" />
          </div>

          <article v-for="(example, i) in lesson.caseNotes || []" :key="`c${i}`" class="xk-mod xk-case">
            <h4 class="xk-mod__title"><XkModIcon name="case" />{{ example.title }}<span class="xk-tag xk-tag--sourced">真实案例</span></h4>
            <p><XkRichText :text="example.text" /></p>
            <p v-if="example.sourceUrl || example.sourceLabel" class="xk-case__source">
              <b>出处</b>
              <a v-if="link(example.sourceUrl)" :href="link(example.sourceUrl)" target="_blank" rel="noreferrer">{{ example.sourceLabel || example.sourceUrl }}</a>
              <span v-else>{{ example.sourceLabel }}</span>
              <span v-if="example.sourceLocator">{{ example.sourceLocator }}</span>
              <span v-if="sourceForCase(example)?.access_status" class="xk-source-scope">引据范围：{{ readingScope(sourceForCase(example).access_status) }}</span>
            </p>
            <p v-if="example.boundary" class="xk-note"><b>适用边界</b><span>{{ example.boundary }}</span></p>
            <a v-if="example.href" class="xk-case__more" :href="link(example.href)">展开这则案例与来源</a>
          </article>

          <section v-if="has(lesson.counterexamples)" class="xk-mod xk-counterexamples">
            <h4 class="xk-mod__title"><XkModIcon name="split" />反例怎样改变判断</h4>
            <article v-for="(example, i) in lesson.counterexamples" :key="i" class="xk-counterexample">
              <p class="xk-counterexample__kind">{{ identityLabel(example.identity) }}</p>
              <p><XkRichText :text="example.text" /></p>
              <p class="xk-note"><b>它限制什么</b><span><XkRichText :text="example.effect" /></span></p>
              <p v-if="example.sourceIds?.length" class="xk-source-links"><a v-for="id in example.sourceIds" :key="id" :href="`#${sourceAnchor(id)}`">{{ (lesson.sources || []).find((source: any) => source.id === id)?.title || id }}</a></p>
            </article>
          </section>

          <section v-if="has(lesson.boundaries)" class="xk-mod xk-limit">
            <h4 class="xk-mod__title"><XkModIcon name="limit" />这一步还不能推出什么</h4>
            <ul><li v-for="(boundary, i) in lesson.boundaries" :key="i"><XkRichText :text="boundary" /></li></ul>
          </section>

          <section v-if="lesson.applicability?.reason || has(lesson.openQuestions)" class="xk-mod xk-open-questions">
            <h4 class="xk-mod__title"><XkModIcon name="terms" />适用范围与待回答的问题</h4>
            <p v-if="lesson.applicability?.reason"><XkRichText :text="lesson.applicability.reason" /></p>
            <ul v-if="has(lesson.openQuestions)"><li v-for="(question, i) in lesson.openQuestions" :key="i"><XkRichText :text="question" /></li></ul>
          </section>

          <section v-if="has(lesson.questions) || has(lesson.questionAnswers)" class="xk-mod xk-check">
            <h4 class="xk-mod__title"><XkModIcon name="check" />读完后，试着辨认</h4>
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
                  <p v-if="answer.basis" class="xk-answer__basis">依据：<XkRichText :text="answer.basis" /></p>
                </div>
              </details>
            </div>
          </section>

          <section v-if="lesson.summary" class="xk-mod xk-summary">
            <h4 class="xk-mod__title"><XkModIcon name="summary" />收束</h4>
            <p><span>{{ lesson.summary }}</span></p>
          </section>

          <nav v-if="has(lesson.caseLinks)" class="xk-lesson__more" aria-label="继续阅读">
            <a v-for="item in lesson.caseLinks" :key="item.href" :href="link(item.href)"><span>{{ item.title }}</span></a>
          </nav>

          <details v-if="has(lesson.sources) || lesson.lecturePath" class="xk-lesson-materials">
            <summary>原文定位、引用资料与完整解读</summary>
            <div class="xk-lesson-materials__body">
              <p v-if="has(lesson.sourceRefs)" class="xk-original-refs"><span v-for="(item, i) in lesson.sourceRefs" :key="i">{{ item.section ? `§${item.section}` : sourceRef }} · 原文第 {{ item.startLine || item.start_line }}—{{ item.endLine || item.end_line }} 行</span></p>
              <nav class="xk-reading-downloads" aria-label="本节阅读材料">
                <a v-if="lesson.lecturePath" :href="link(lesson.lecturePath)" download>完整解读原稿</a>
                <a v-if="lesson.sourceSlicePath" :href="link(lesson.sourceSlicePath)" download>原文对照</a>
                <a v-if="lesson.sourcesPath" :href="link(lesson.sourcesPath)" download>来源登记</a>
                <a v-if="lesson.diagramsPath" :href="link(lesson.diagramsPath)" download>图解材料</a>
                <a v-for="file in lesson.supplementaryFiles || []" :key="file.path" :href="link(file.path)" download>{{ file.title || file.label || file.name || '补充数据' }}</a>
              </nav>
              <p class="xk-materials-note">以下资料支持本节的具体论述，实际阅读范围和适用限制在各条记录中注明。</p>
              <article v-for="source in lesson.sources || []" :id="sourceAnchor(source.id)" :key="source.id" class="xk-source-entry">
                <h5><a v-if="link(source.url)" :href="link(source.url)" target="_blank" rel="noreferrer">{{ source.title }}</a><span v-else>{{ source.title }}</span></h5>
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
