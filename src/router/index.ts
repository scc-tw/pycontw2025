import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/views/HomePage.vue'
import SourceCode from '@/views/SourceCode.vue'
import BenchmarkData from '@/views/BenchmarkData.vue'

const router = createRouter({
  // Use history mode for clean URLs with custom domain
  history: createWebHistory(import.meta.env.BASE_URL),
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