import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'
import FeedbackExplorer from './FeedbackExplorer.vue'
import ReadingTools from './ReadingTools.vue'
import JointExplorer from './JointExplorer.vue'
import PredictionExplorer from './PredictionExplorer.vue'
import SectionLesson from './SectionLesson.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout: () => h(DefaultTheme.Layout, null, {
    'doc-before': () => h(ReadingTools)
  }),
  enhanceApp({ app }) {
    app.component('FeedbackExplorer', FeedbackExplorer)
    app.component('JointExplorer', JointExplorer)
    app.component('PredictionExplorer', PredictionExplorer)
    app.component('SectionLesson', SectionLesson)
  }
} satisfies Theme
