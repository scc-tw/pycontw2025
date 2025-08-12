import { createRouter, createWebHashHistory } from 'vue-router'
import HomePage from '@/views/HomePage.vue'
import SourceCode from '@/views/SourceCode.vue'
import BenchmarkData from '@/views/BenchmarkData.vue'

const router = createRouter({
  // Use hash mode for GitHub Pages compatibility
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage
    },
    {
      path: '/source',
      name: 'source',
      component: SourceCode
    },
    {
      path: '/data',
      name: 'data',
      component: BenchmarkData
    }
  ]
})

export default router