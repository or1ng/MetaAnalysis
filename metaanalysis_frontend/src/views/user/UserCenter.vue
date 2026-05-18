<template>
  <div>
    <div class="page-header">
      <h2>个人中心</h2>
    </div>

    <div class="user-layout">
      <!-- 左侧：菜单 -->
      <div class="nav-panel page-card">
        <el-menu :default-active="activeTab" @select="activeTab = $event">
          <el-menu-item index="profile"><el-icon><User /></el-icon>个人资料</el-menu-item>
          <el-menu-item index="projects"><el-icon><Folder /></el-icon>项目管理</el-menu-item>
          <el-menu-item index="files"><el-icon><Files /></el-icon>文件仓库</el-menu-item>
          <el-menu-item index="history"><el-icon><Clock /></el-icon>使用记录</el-menu-item>
          <el-menu-item index="security"><el-icon><Lock /></el-icon>账号安全</el-menu-item>
        </el-menu>
      </div>

      <!-- 右侧：内容面板 -->
      <div class="content-panel page-card">
        <!-- 个人资料 -->
        <div v-if="activeTab === 'profile'">
          <h3>个人资料</h3>
          <el-form label-width="100px" style="max-width:500px;margin-top:20px">
            <el-form-item label="用户名">
              <el-input v-model="profile.username" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profile.email" />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag>{{ profile.role }}</el-tag>
            </el-form-item>
            <el-form-item label="注册时间">
              <span>{{ profile.created_at }}</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="ElMessage.success('保存成功')">保存修改</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 存储用量 -->
        <div class="storage-section">
          <h3>存储用量</h3>
          <div style="max-width:400px;margin-top:12px">
            <el-progress :percentage="storagePercent" :color="storagePercent > 80 ? '#ff4d4f' : '#3a6fd8'" />
            <div style="display:flex;justify-content:space-between;font-size:12px;color:#909399;margin-top:4px">
              <span>{{ formatSize(storageUsed) }} 已使用</span>
              <span>{{ formatSize(storageLimit) }} 总容量</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const activeTab = ref('profile')
const storageUsed = ref(268435456)
const storageLimit = ref(536870912)
const storagePercent = computed(() => Math.round((storageUsed.value / storageLimit.value) * 100))

const profile = ref({
  username: 'demo_user',
  email: 'demo@metaanalysis.com',
  role: '专业版用户',
  created_at: '2026-04-15',
})

function formatSize(bytes) {
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(0) + ' MB'
}
</script>

<style scoped>
.user-layout { display: grid; grid-template-columns: 180px 1fr; gap: 16px; }
.nav-panel .el-menu { border-right: none; }
.storage-section { margin-top: 30px; }
</style>
