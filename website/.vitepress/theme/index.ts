import type { Theme } from 'vitepress'
import Layout from './Layout.vue'
import SectionLesson from './components/lesson/SectionLesson.vue'
import FeedbackExplorer from './components/explorers/FeedbackExplorer.vue'
import JointExplorer from './components/explorers/JointExplorer.vue'
import PredictionExplorer from './components/explorers/PredictionExplorer.vue'
import { installPageTurns } from './composables/transitions'
import 'vitepress/dist/client/theme-default/styles/icons.css'
import './styles/index.css'

export default {
  Layout,
  enhanceApp({ app, router, siteData }) {
    app.component('SectionLesson', SectionLesson)
    app.component('FeedbackExplorer', FeedbackExplorer)
    app.component('JointExplorer', JointExplorer)
    app.component('PredictionExplorer', PredictionExplorer)
    if (typeof window !== 'undefined') installPageTurns(router, siteData)
  }
} satisfies Theme
