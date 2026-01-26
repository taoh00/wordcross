import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('./views/Home.vue')
  },
  {
    path: '/game/:mode',
    name: 'Game',
    component: () => import('./views/Game.vue')
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: () => import('./views/Leaderboard.vue')
  },
  {
    path: '/test-mode',
    name: 'TestMode',
    component: () => import('./views/TestMode.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('./views/Settings.vue')
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('./views/Admin.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
