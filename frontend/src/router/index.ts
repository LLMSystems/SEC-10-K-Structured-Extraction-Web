import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import ResultView from '@/views/ResultView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/result/:jobId', name: 'result', component: ResultView, props: true },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminView.vue'),
    },
    {
      path: '/admin/filings/:accession',
      name: 'admin-filing',
      component: () => import('@/views/AdminFilingDetailView.vue'),
      props: true,
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
