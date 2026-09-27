import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'overview', component: () => import('../views/OverviewView.vue') },
  { path: '/board', name: 'board', component: () => import('../views/BoardView.vue') },
  { path: '/list', name: 'list', component: () => import('../views/ListView.vue') },
  { path: '/manage', name: 'manage', component: () => import('../views/ManageView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
