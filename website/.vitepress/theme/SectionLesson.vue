<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import lessons from '../../content/section-lessons.json'
import FeedbackExplorer from './FeedbackExplorer.vue'
import JointExplorer from './JointExplorer.vue'
import PredictionExplorer from './PredictionExplorer.vue'
const props = defineProps<{ section: string }>()
const lesson = computed(() => (lessons.lessons as Record<string, any>)[props.section])
const sectionLabel = computed(() => /^(?:\d+|[A-D])(?:\.\d+)+$/.test(props.section) ? `§${props.section}` : lesson.value?.title || '本段')
const link = (href: string) => {
  if (/^https?:/.test(href)) return href
  const value = href.replace(/^\.\.\//, '/').replace(/^\.\//, '/')
  const [path, fragment] = value.split('#')
  return withBase((path.endsWith('/') || /\.[a-z]+$/i.test(path) ? path : path + '.html') + (fragment ? '#' + fragment : ''))
}
</script>

<template>
  <section v-if="lesson" class="section-lesson" :id="`lesson-${section.toLowerCase().replaceAll('.', '-')}`" :aria-label="`${sectionLabel} 讲解`">
    <header class="lesson-heading"><h3 :id="`explain-${section.toLowerCase().replaceAll('.', '-')}`">读懂这一节</h3><span>{{ sectionLabel }} · 讲解</span></header>
    <p class="lesson-lead">{{ lesson.lead }}</p>
    <p v-for="paragraph in lesson.explanation" :key="paragraph">{{ paragraph }}</p>
    <div v-if="lesson.argumentSteps?.length"><h4>论证怎样展开</h4><ol><li v-for="step in lesson.argumentSteps" :key="step">{{ step }}</li></ol></div>
    <div class="lesson-distinctions" v-if="lesson.distinctions?.length">
      <h4>把容易混淆的地方分开</h4>
      <dl v-for="(distinction, i) in lesson.distinctions" :key="i">
        <div><dt>{{ distinction.leftTitle }}</dt><dd>{{ distinction.leftText }}</dd></div>
        <div><dt>{{ distinction.rightTitle }}</dt><dd>{{ distinction.rightText }}</dd></div>
      </dl>
    </div>
    <figure v-if="lesson.diagramPath" class="concept-figure lesson-figure"><img :src="withBase(lesson.diagramPath)" :alt="lesson.title"><figcaption>{{ lesson.diagramCaption || '配合本节阅读的关系示意；图中成立条件与正文一起理解。' }}</figcaption></figure>
    <figure v-for="figure in lesson.figures || []" :key="figure.path" class="concept-figure lesson-figure"><img :src="withBase(figure.path)" :alt="figure.alt"><figcaption>{{ figure.caption }}</figcaption></figure>
    <div v-for="(example, i) in lesson.teachingExamples || []" :key="`teaching-${i}`"><h4>{{ example.title }} · 教学情景</h4><p v-if="example.assumptions" class="source-note">设定：{{ example.assumptions }}</p><p>{{ example.text }}</p><p v-if="example.boundary">{{ example.boundary }}</p></div>
    <FeedbackExplorer v-if="section === '3.3'" />
    <JointExplorer v-if="section === 'C.12'" />
    <PredictionExplorer v-if="section === '4.6'" />
    <div class="lesson-case" v-for="(example, i) in lesson.caseNotes || []" :key="i">
      <h4>{{ example.title }}</h4>
      <p>{{ example.text }}</p>
      <p class="source-note"><a :href="example.sourceUrl" target="_blank" rel="noreferrer">{{ example.sourceLabel }}</a><span v-if="example.sourceLocator"> · {{ example.sourceLocator }}</span></p>
      <p>{{ example.boundary }}</p>
      <a v-if="example.href" :href="link(example.href)">展开这则案例与来源 →</a>
    </div>
    <div class="lesson-boundaries"><h4>这一步还不能推出什么</h4><ul><li v-for="boundary in lesson.boundaries" :key="boundary">{{ boundary }}</li></ul></div>
    <div class="lesson-questions"><h4>读完后，试着辨认</h4><ol><li v-for="question in lesson.questions" :key="question">{{ question }}</li></ol></div>
    <details v-for="(answer, i) in lesson.questionAnswers || []" :key="`answer-${i}`" class="lesson-answer"><summary>{{ answer.question }} · 查看解释</summary><p>{{ answer.answer }}</p><p v-if="answer.basis" class="source-note">依据：{{ answer.basis }}</p></details>
    <p v-if="lesson.caseLinks?.length" class="lesson-further"><a v-for="item in lesson.caseLinks" :key="item.href" :href="link(item.href)">{{ item.title }} →</a></p>
  </section>
</template>
