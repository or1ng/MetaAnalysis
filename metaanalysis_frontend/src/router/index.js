import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    redirect: '/home',
    children: [
      { path: 'home', name: 'Dashboard', component: () => import('../views/home/Dashboard.vue'), meta: { title: '工作台' } },
      { path: 'data', name: 'DataManage', component: () => import('../views/data/DataManage.vue'), meta: { title: '数据中心' } },
      { path: 'clean', name: 'DataClean', component: () => import('../views/clean/DataClean.vue'), meta: { title: '智能清洗' } },
      { path: 'ai-chat', name: 'AiChat', component: () => import('../views/aiChat/AiChat.vue'), meta: { title: 'AI问答' } },
      { path: 'statistic', name: 'Statistics', component: () => import('../views/statistic/Statistics.vue'), meta: { title: '统计分析' } },
      { path: 'chart', name: 'ChartStudio', component: () => import('../views/chart/ChartStudio.vue'), meta: { title: '可视化' } },
      { path: 'report', name: 'ReportGen', component: () => import('../views/report/ReportGen.vue'), meta: { title: '报告中心' } },
      { path: 'user', name: 'UserCenter', component: () => import('../views/user/UserCenter.vue'), meta: { title: '个人中心' } },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'MetaAnalysis'} - MetaAnalysis元析智能`
  next()
})

export default router
