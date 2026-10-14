import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'
import HomeView from './HomeView.vue'
import FeedbackExplorer from './FeedbackExplorer.vue'
import ReadingTools from './ReadingTools.vue'
import JointExplorer from './JointExplorer.vue'
import PredictionExplorer from './PredictionExplorer.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout: () => h(DefaultTheme.Layout, null, {
    'doc-before': () => h(ReadingTools)
  }),
  enhanceApp({ app }) {
    app.component('HomeView', HomeView)
    app.component('FeedbackExplorer', FeedbackExplorer)
    app.component('JointExplorer', JointExplorer)
    app.component('PredictionExplorer', PredictionExplorer)
  }
} satisfies Theme
