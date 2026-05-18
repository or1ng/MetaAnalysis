<template>
  <el-container class="main-layout">
    <!-- 左侧导航 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo-area">
        <img src="https://api.iconify.design/fluent:data-bar-vertical-24-filled.svg?color=%233a6fd8" alt="logo" class="logo-icon" />
        <span v-show="!isCollapse" class="logo-text">MetaAnalysis</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        background-color="#1e293b"
        text-color="#94a3b8"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/home">
          <el-icon><HomeFilled /></el-icon>
          <span>工作台</span>
        </el-menu-item>

        <el-menu-item index="/data">
          <el-icon><UploadFilled /></el-icon>
          <span>数据中心</span>
        </el-menu-item>

        <el-menu-item index="/clean">
          <el-icon><Brush /></el-icon>
          <span>智能清洗</span>
        </el-menu-item>

        <el-menu-item index="/ai-chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI问答</span>
        </el-menu-item>

        <el-menu-item index="/statistic">
          <el-icon><DataAnalysis /></el-icon>
          <span>统计分析</span>
        </el-menu-item>

        <el-menu-item index="/chart">
          <el-icon><PieChart /></el-icon>
          <span>可视化</span>
        </el-menu-item>

        <el-menu-item index="/report">
          <el-icon><Document /></el-icon>
          <span>报告中心</span>
        </el-menu-item>

        <el-menu-item index="/user">
          <el-icon><UserFilled /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>

      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon :size="18">
          <DArrowLeft v-if="!isCollapse" />
          <DArrowRight v-else />
        </el-icon>
      </div>
    </el-aside>

    <el-container>
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>MetaAnalysis</el-breadcrumb-item>
            <el-breadcrumb-item>{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-badge :value="3" :max="99" class="msg-badge">
            <el-icon :size="20" class="header-icon"><Bell /></el-icon>
          </el-badge>
          <el-icon :size="20" class="header-icon"><Setting /></el-icon>
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="30" class="user-avatar">{{ userStore.username.charAt(0) }}</el-avatar>
              <span class="user-name">{{ userStore.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/user')">
                  <el-icon><UserFilled /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>

      <!-- 底部状态栏 -->
      <el-footer height="36px" class="footer">
        <span>MetaAnalysis元析智能 v1.0.0</span>
        <span>|</span>
        <span>{{ currentTime }}</span>
        <span>|</span>
        <span>数据库连接正常</span>
      </el-footer>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../store/index'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)
const currentTime = ref('')
let timer = null

const currentRoute = computed(() => route.path)

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', { hour12: false })
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: #1e293b;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.logo-area {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: 1px solid #334155;
  flex-shrink: 0;
}
.logo-icon { width: 28px; height: 28px; }
.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
}

.sidebar .el-menu {
  flex: 1;
  border-right: none;
}
.sidebar .el-menu-item {
  height: 48px;
  line-height: 48px;
}
.sidebar .el-menu-item.is-active {
  background: #334155 !important;
}

.collapse-btn {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
  border-top: 1px solid #334155;
  flex-shrink: 0;
}
.collapse-btn:hover { color: #fff; }

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  color: var(--text-secondary);
  cursor: pointer;
}
.header-icon:hover { color: var(--primary); }

.msg-badge { line-height: 1; }

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-primary);
}
.user-avatar { background: var(--primary); color: #fff; font-size: 14px; }
.user-name { font-size: 14px; }

.main-content {
  background: var(--bg-color);
  padding: 20px;
  overflow-y: auto;
}

.footer {
  background: #fff;
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
