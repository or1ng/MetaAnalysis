<template>
  <div class="dashboard">
    <!-- 数据统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background:#eff6ff"><el-icon :size="24" color="#3a6fd8"><FolderOpened /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">12</div>
          <div class="stat-label">我的数据集</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#f0f9ff"><el-icon :size="24" color="#0ea5e9"><List /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">36</div>
          <div class="stat-label">分析任务</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#f0fdf4"><el-icon :size="24" color="#22c55e"><Document /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">8</div>
          <div class="stat-label">已生成报告</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#fef3c7"><el-icon :size="24" color="#f59e0b"><Coin /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">256 MB</div>
          <div class="stat-label">已用存储</div>
        </div>
      </div>
    </div>

    <!-- 快捷功能入口 -->
    <div class="page-card">
      <h3 class="section-title">快捷功能</h3>
      <div class="quick-actions">
        <div class="action-item" @click="$router.push('/data')">
          <el-icon :size="32" color="#3a6fd8"><UploadFilled /></el-icon>
          <span>上传数据</span>
        </div>
        <div class="action-item" @click="$router.push('/clean')">
          <el-icon :size="32" color="#8b5cf6"><Brush /></el-icon>
          <span>智能清洗</span>
        </div>
        <div class="action-item" @click="$router.push('/ai-chat')">
          <el-icon :size="32" color="#06b6d4"><ChatDotRound /></el-icon>
          <span>AI问答</span>
        </div>
        <div class="action-item" @click="$router.push('/statistic')">
          <el-icon :size="32" color="#f59e0b"><DataAnalysis /></el-icon>
          <span>统计分析</span>
        </div>
        <div class="action-item" @click="$router.push('/chart')">
          <el-icon :size="32" color="#22c55e"><PieChart /></el-icon>
          <span>制作图表</span>
        </div>
        <div class="action-item" @click="$router.push('/report')">
          <el-icon :size="32" color="#ef4444"><Document /></el-icon>
          <span>生成报告</span>
        </div>
      </div>
    </div>

    <!-- 最近项目 -->
    <div class="page-card">
      <h3 class="section-title">最近项目</h3>
      <el-table :data="recentProjects" stripe style="width:100%">
        <el-table-column prop="name" label="项目名称" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '已完成' ? 'success' : row.status === '进行中' ? 'warning' : 'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="更新时间" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
const recentProjects = [
  { name: '2024年Q1销售数据分析', type: '统计分析', status: '已完成', date: '2026-05-13 18:30' },
  { name: '客户满意度调查清洗', type: '数据清洗', status: '进行中', date: '2026-05-13 16:20' },
  { name: '产品A/B测试报告', type: '报告生成', status: '已完成', date: '2026-05-12 14:00' },
  { name: '年度财务数据汇总', type: '数据上传', status: '已完成', date: '2026-05-11 10:15' },
]
</script>

<style scoped>
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-icon {
  width: 48px; height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.section-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: var(--text-primary); }
.quick-actions {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
}
.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.action-item:hover {
  background: #f5f7fa;
  transform: translateY(-2px);
}
.action-item span { font-size: 13px; color: var(--text-regular); }
</style>
