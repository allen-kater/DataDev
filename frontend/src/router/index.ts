import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/asset' },
    {
      path: '/asset',
      name: 'asset',
      component: () => import('@/views/asset/AssetView.vue'),
    },
    {
      path: '/sql',
      name: 'sql',
      component: () => import('@/views/sql/SqlView.vue'),
    },
    {
      path: '/schedule',
      name: 'schedule',
      component: () => import('@/views/schedule/ScheduleView.vue'),
    },
    {
      path: '/ai',
      name: 'ai',
      component: () => import('@/views/ai/AiView.vue'),
    },
    {
      path: '/system',
      name: 'system',
      component: () => import('@/views/system/SystemView.vue'),
    },
  ],
})

export default router
