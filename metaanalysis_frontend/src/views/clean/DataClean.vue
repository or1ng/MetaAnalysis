<template>
  <div>
    <div class="page-header">
      <h2>智能数据清洗</h2>
      <div class="header-actions" v-if="selectedDataset">
        <el-button @click="handleRestore" :disabled="!currentDataset?.is_cleaned">
          <el-icon><RefreshLeft /></el-icon>还原原始数据
        </el-button>
        <el-button type="success" @click="handleSave" :disabled="!hasUnsavedChanges">
          <el-icon><Check /></el-icon>确认并保存
        </el-button>
      </div>
    </div>

    <!-- 数据集选择 -->
    <div class="dataset-selector page-card" v-if="!selectedDataset">
      <h3>选择要清洗的数据集</h3>
      <el-table :data="datasetList" stripe size="small" @row-click="handleSelectDataset"
        style="width:100%; cursor:pointer">
        <el-table-column prop="name" label="数据集名称" />
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{row}">
            <el-tag size="small">{{ row.file_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="row_count" label="行数" width="100" />
        <el-table-column prop="col_count" label="列数" width="80" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
      </el-table>
    </div>

    <!-- 三栏清洗界面 -->
    <div class="clean-layout" v-if="selectedDataset">
      <!-- 左：字段列表 -->
      <div class="field-panel page-card">
        <h3>字段列表（{{ fields.length }}个）</h3>
        <el-select v-model="fieldFilter" size="small" style="width:100%;margin-bottom:10px" placeholder="筛选字段">
          <el-option label="全部字段" value="all" />
          <el-option label="有缺失" value="missing" />
          <el-option label="数值型" value="numeric" />
          <el-option label="文本型" value="string" />
        </el-select>
        <div class="field-list">
          <div v-for="field in filteredFields" :key="field.name"
            class="field-item" :class="{ active: selectedField === field.name }"
            @click="selectedField = field.name">
            <span class="f-name">{{ field.name }}</span>
            <el-tag :type="getFieldTypeTag(field.type)" size="small">{{ field.type }}</el-tag>
            <span class="f-miss" v-if="field.missing_count > 0"
              :class="getMissClass(field.missing_rate)">
              {{ (field.missing_rate * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- 中：数据预览 -->
      <div class="preview-panel page-card">
        <div class="preview-toolbar">
          <span class="toolbar-title">数据预览</span>
          <el-tag v-if="previewMeta.outlier_count > 0" type="danger" size="small">
            异常值 {{ previewMeta.outlier_count }}
          </el-tag>
          <el-tag v-if="previewMeta.missing_count > 0" type="warning" size="small">
            缺失值 {{ previewMeta.missing_count }}
          </el-tag>
          <el-tag v-if="previewMeta.dup_count > 0" type="info" size="small">
            重复行 {{ previewMeta.dup_count }}
          </el-tag>
          <span class="toolbar-hint" v-if="previewMeta.rows">
            显示前{{ previewMeta.rows.length }}行
          </span>
        </div>
        <div class="table-container">
          <el-table :data="previewMeta.rows || []" stripe size="small" border
            style="width:100%" max-height="420">
            <el-table-column type="index" label="#" width="45" />
            <el-table-column v-for="col in (previewMeta.columns || [])" :key="col"
              :prop="col" :label="col" min-width="100">
              <template #default="{row}">
                <span :class="getCellClass(row, col)">{{ formatCellValue(row, col) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="previewLoading" description="加载中..." :image-size="40" />
          <el-empty v-else-if="!previewMeta.rows?.length" description="暂无数据" :image-size="40" />
        </div>

        <!-- 底部日志栏 -->
        <div class="log-bar" v-if="cleanLogs.length > 0">
          <div v-for="log in cleanLogs.slice(0, 3)" :key="log.id" class="log-item">
            <span class="log-dot" :style="{ background: getLogColor(log.action_type) }"></span>
            <span>{{ log.result_summary }}</span>
          </div>
          <span class="log-more" v-if="cleanLogs.length > 3" @click="logDrawerVisible = true">
            查看完整日志
          </span>
        </div>
      </div>

      <!-- 右：清洗操作面板 -->
      <div class="clean-panel page-card">
        <!-- 质量诊断 -->
        <div class="panel-section">
          <h4>质量诊断</h4>
          <div class="stat-row" v-for="item in qualityStats" :key="item.label">
            <span class="stat-label">{{ item.label }}</span>
            <span class="stat-value" :class="item.cls">{{ item.value }}</span>
          </div>
        </div>

        <!-- 一键智能清洗 -->
        <div class="panel-section">
          <h4>一键智能清洗</h4>
          <p class="section-desc">自动处理全部异常值、缺失值、重复行和格式问题</p>
          <el-button type="primary" style="width:100%" :loading="cleaning" @click="handleAutoClean">
            <el-icon><MagicStick /></el-icon>一键智能清洗
          </el-button>
        </div>

        <!-- 自定义清洗 -->
        <div class="panel-section">
          <h4>自定义清洗</h4>

          <div class="option-row">
            <div class="option-label">
              <span>缺失值处理</span>
              <small>数值型字段</small>
            </div>
            <el-select v-model="customConfig.missing_strategy" size="small" style="width:120px">
              <el-option label="均值填充" value="mean" />
              <el-option label="中位数填充" value="median" />
              <el-option label="众数填充" value="mode" />
              <el-option label="删除行" value="drop" />
              <el-option label="自定义值" value="constant" />
            </el-select>
          </div>

          <div class="option-row">
            <div class="option-label">
              <span>异常值检测</span>
              <small>IQR / Z-Score</small>
            </div>
            <el-select v-model="customConfig.outlier_method" size="small" style="width:120px">
              <el-option label="IQR法" value="iqr" />
              <el-option label="Z-Score" value="zscore" />
            </el-select>
          </div>

          <div class="option-row">
            <div class="option-label">
              <span>异常值处理</span>
              <small>截断/替换/删除</small>
            </div>
            <el-select v-model="customConfig.outlier_handle" size="small" style="width:120px">
              <el-option label="截断边界" value="clip" />
              <el-option label="替换均值" value="mean" />
              <el-option label="删除行" value="drop" />
            </el-select>
          </div>

          <div class="option-row">
            <div class="option-label"><span>去除重复行</span></div>
            <el-switch v-model="customConfig.remove_duplicates" />
          </div>

          <div class="option-row">
            <div class="option-label"><span>去除首尾空白</span></div>
            <el-switch v-model="customConfig.strip_whitespace" />
          </div>

          <div class="option-row">
            <div class="option-label"><span>日期格式统一</span></div>
            <el-switch v-model="customConfig.date_unify" />
          </div>

          <el-button type="warning" style="width:100%;margin-top:10px" :loading="cleaning"
            @click="handleCustomClean">
            <el-icon><Setting /></el-icon>执行自定义清洗
          </el-button>
        </div>

        <!-- 操作日志 -->
        <div class="panel-section">
          <h4>操作日志</h4>
          <div class="log-list">
            <div v-for="log in cleanLogs" :key="log.id" class="log-entry">
              <span class="log-dot" :style="{ background: getLogColor(log.action_type) }"></span>
              <div class="log-content">
                <div class="log-text">{{ log.action_type }}：{{ log.result_summary }}</div>
                <div class="log-time">{{ log.created_at }}</div>
              </div>
              <el-button v-if="log.has_snapshot" size="small" text type="primary"
                @click="handleRollback(log.id)">回滚</el-button>
            </div>
            <el-empty v-if="cleanLogs.length === 0" description="暂无清洗记录" :image-size="40" />
          </div>
        </div>
      </div>
    </div>

    <!-- 清洗结果对话框 -->
    <el-dialog v-model="resultDialogVisible" title="清洗结果" width="520px">
      <div v-if="cleanResult">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="清洗前行数">{{ cleanResult.before_rows }}</el-descriptions-item>
          <el-descriptions-item label="清洗后行数">{{ cleanResult.after_rows }}</el-descriptions-item>
          <el-descriptions-item label="清洗前评分">
            <el-tag :type="getScoreTag(cleanResult.before_score)">{{ cleanResult.before_score }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="清洗后评分">
            <el-tag :type="getScoreTag(cleanResult.after_score)">{{ cleanResult.after_score }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:16px 0 8px">操作明细</h4>
        <el-timeline>
          <el-timeline-item v-for="(log, i) in cleanResult.logs" :key="i"
            :type="log.affected > 0 ? 'primary' : 'info'" :hollow="log.affected === 0">
            <strong>{{ log.action }}</strong>
            <span style="color:var(--el-text-secondary);margin-left:8px">{{ log.summary }}</span>
          </el-timeline-item>
        </el-timeline>
      </div>
      <template #footer>
        <el-button @click="resultDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDatasets } from '@/api/dataset'
import { autoClean, customClean, getCleanSummary, getCleanLogs, getCleanPreview, rollbackClean, restoreDataset } from '@/api/clean'

// ── 数据集列表 ──
const datasetList = ref([])
const selectedDataset = ref(null)
const currentDataset = ref(null)
const hasUnsavedChanges = ref(false)

// ── 字段列表 ──
const fields = ref([])
const fieldFilter = ref('all')
const selectedField = ref(null)
const filteredFields = computed(() => {
  if (fieldFilter.value === 'all') return fields.value
  if (fieldFilter.value === 'missing') return fields.value.filter(f => f.missing_count > 0)
  if (fieldFilter.value === 'numeric') return fields.value.filter(f => f.type === 'integer' || f.type === 'float')
  if (fieldFilter.value === 'string') return fields.value.filter(f => f.type === 'string')
  return fields.value
})

// ── 质量诊断 ──
const qualitySummary = ref(null)
const qualityStats = computed(() => {
  if (!qualitySummary.value) return []
  const q = qualitySummary.value
  return [
    { label: '总行数', value: q.total_rows?.toLocaleString() || '-', cls: 'val-ok' },
    { label: '异常值', value: `${q.outlier_count || 0} 行`, cls: q.outlier_count > 0 ? 'val-danger' : 'val-ok' },
    { label: '缺失值', value: `${q.missing_cells || 0} 处`, cls: q.missing_cells > 0 ? 'val-warn' : 'val-ok' },
    { label: '重复行', value: `${q.dup_rows || 0} 行`, cls: q.dup_rows > 0 ? 'val-warn' : 'val-ok' },
    { label: '质量评分', value: `${q.score || 0} / 100`, cls: q.score >= 80 ? 'val-ok' : q.score >= 60 ? 'val-warn' : 'val-danger' },
  ]
})

// ── 预览 ──
const previewMeta = ref({ rows: [], columns: [], outlier_count: 0, missing_count: 0, dup_count: 0 })
const previewLoading = ref(false)

// ── 清洗配置 ──
const cleaning = ref(false)
const customConfig = reactive({
  missing_strategy: 'mean',
  outlier_method: 'iqr',
  outlier_handle: 'clip',
  remove_duplicates: true,
  strip_whitespace: true,
  date_unify: true,
})

// ── 日志 ──
const cleanLogs = ref([])

// ── 结果 ──
const cleanResult = ref(null)
const resultDialogVisible = ref(false)

// ── 加载数据集列表 ──
async function loadDatasets() {
  try {
    const res = await getDatasets({ page: 1, page_size: 50 })
    datasetList.value = res.data?.items || res.data || []
  } catch (e) {
    console.error(e)
  }
}

// ── 选择数据集 ──
async function handleSelectDataset(row) {
  selectedDataset.value = row.id
  currentDataset.value = row
  hasUnsavedChanges.value = false
  cleanLogs.value = []
  await Promise.all([loadSummary(), loadPreview(), loadLogs()])
}

// ── 加载质量诊断 ──
async function loadSummary() {
  if (!selectedDataset.value) return
  try {
    const res = await getCleanSummary(selectedDataset.value)
    qualitySummary.value = res.data
    // 更新字段列表
    const q = res.data
    if (q.missing_detail) {
      const missingMap = {}
      q.missing_detail.forEach(m => {
        missingMap[m.column] = { count: m.missing_count, rate: m.missing_rate / 100 }
      })
      fields.value = (currentDataset.value?.columns_json || []).map(col => ({
        name: col.name,
        type: col.type,
        missing_count: missingMap[col.name]?.count || 0,
        missing_rate: missingMap[col.name]?.rate || 0,
      }))
    }
  } catch (e) {
    console.error(e)
  }
}

// ── 加载预览 ──
async function loadPreview() {
  if (!selectedDataset.value) return
  previewLoading.value = true
  try {
    const res = await getCleanPreview(selectedDataset.value, { rows: 50 })
    previewMeta.value = res.data || { rows: [], columns: [], outlier_count: 0, missing_count: 0, dup_count: 0 }
  } catch (e) {
    console.error(e)
  } finally {
    previewLoading.value = false
  }
}

// ── 加载日志 ──
async function loadLogs() {
  if (!selectedDataset.value) return
  try {
    const res = await getCleanLogs(selectedDataset.value, { page: 1, page_size: 20 })
    cleanLogs.value = res.data?.items || []
  } catch (e) {
    console.error(e)
  }
}

// ── 一键清洗 ──
async function handleAutoClean() {
  cleaning.value = true
  try {
    const res = await autoClean(selectedDataset.value)
    cleanResult.value = res.data
    resultDialogVisible.value = true
    hasUnsavedChanges.value = true
    await Promise.all([loadSummary(), loadPreview(), loadLogs()])
    // 刷新数据集列表
    await loadDatasets()
    currentDataset.value = datasetList.value.find(d => d.id === selectedDataset.value)
    ElMessage.success(`清洗完成！质量评分 ${res.data.before_score} → ${res.data.after_score}`)
  } catch (e) {
    ElMessage.error('清洗失败：' + (e.response?.data?.message || e.message))
  } finally {
    cleaning.value = false
  }
}

// ── 自定义清洗 ──
async function handleCustomClean() {
  cleaning.value = true
  try {
    const res = await customClean(selectedDataset.value, { ...customConfig })
    cleanResult.value = res.data
    resultDialogVisible.value = true
    hasUnsavedChanges.value = true
    await Promise.all([loadSummary(), loadPreview(), loadLogs()])
    await loadDatasets()
    currentDataset.value = datasetList.value.find(d => d.id === selectedDataset.value)
    ElMessage.success('自定义清洗完成')
  } catch (e) {
    ElMessage.error('清洗失败：' + (e.response?.data?.message || e.message))
  } finally {
    cleaning.value = false
  }
}

// ── 回滚 ──
async function handleRollback(logId) {
  try {
    await ElMessageBox.confirm('确定回滚到该操作之前的状态？', '回滚确认', { type: 'warning' })
    await rollbackClean(logId)
    ElMessage.success('回滚成功')
    await Promise.all([loadSummary(), loadPreview(), loadLogs()])
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('回滚失败')
  }
}

// ── 还原原始 ──
async function handleRestore() {
  try {
    await ElMessageBox.confirm('确定还原到原始数据？所有清洗记录将被清除。', '还原确认', { type: 'warning' })
    await restoreDataset(selectedDataset.value)
    hasUnsavedChanges.value = false
    ElMessage.success('已还原到原始数据')
    await Promise.all([loadSummary(), loadPreview(), loadLogs()])
    await loadDatasets()
    currentDataset.value = datasetList.value.find(d => d.id === selectedDataset.value)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('还原失败')
  }
}

// ── 保存（刷新数据集状态） ──
function handleSave() {
  hasUnsavedChanges.value = false
  ElMessage.success('清洗结果已保存')
}

// ── 辅助方法 ──
function getFieldTypeTag(type) {
  const map = { integer: '', float: 'warning', string: 'info', datetime: 'success', boolean: 'success' }
  return map[type] || 'info'
}

function getMissClass(rate) {
  if (rate >= 0.1) return 'miss-high'
  if (rate >= 0.03) return 'miss-mid'
  return 'miss-low'
}

function getCellClass(row, col) {
  const key = `_cell_${col}`
  if (row[key] === 'outlier') return 'cell-outlier'
  if (row[key] === 'missing') return 'cell-missing'
  return ''
}

function formatCellValue(row, col) {
  const val = row[col]
  if (val === null || val === undefined) return 'NULL'
  if (typeof val === 'number') return val.toLocaleString()
  return String(val)
}

function getLogColor(action) {
  const map = {
    '去重': '#409eff',
    '异常值截断': '#f56c6c',
    '缺失值填充': '#e6a23c',
    '格式标准化': '#67c23a',
  }
  return map[action] || '#909399'
}

function getScoreTag(score) {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

onMounted(loadDatasets)
</script>

<style scoped>
.clean-layout {
  display: grid;
  grid-template-columns: 220px 1fr 300px;
  gap: 16px;
  min-height: calc(100vh - 160px);
}

.field-panel h4, .preview-panel h4, .clean-panel h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

/* 字段列表 */
.field-list {
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 8px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.15s;
}

.field-item:hover { background: #f5f7fa; }
.field-item.active { background: #ecf5ff; border-left: 3px solid var(--el-color-primary); }

.f-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.f-miss {
  font-size: 11px;
  padding: 1px 5px;
  border-radius: 3px;
  flex-shrink: 0;
}

.miss-low { background: #ecfdf5; color: #10b981; }
.miss-mid { background: #fffbeb; color: #f59e0b; }
.miss-high { background: #fef2f2; color: #ef4444; }

/* 预览面板 */
.preview-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.toolbar-title {
  font-size: 13px;
  font-weight: 600;
  flex: 1;
}

.toolbar-hint {
  font-size: 11px;
  color: var(--el-text-secondary);
}

.table-container {
  overflow-x: auto;
}

.cell-outlier {
  color: #e6a23c;
  font-weight: 600;
  background: #fff7ed;
  padding: 0 4px;
  border-radius: 3px;
}

.cell-missing {
  color: #f56c6c;
  font-style: italic;
  background: #fef2f2;
  padding: 0 4px;
  border-radius: 3px;
}

/* 底部日志栏 */
.log-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  margin-top: 10px;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: var(--el-text-secondary);
  flex-wrap: wrap;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.log-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.log-more {
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 12px;
}

/* 清洗面板 */
.clean-panel {
  max-height: calc(100vh - 160px);
  overflow-y: auto;
}

.panel-section {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.panel-section:last-child { border-bottom: none; }

.panel-section h4 {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-desc {
  font-size: 12px;
  color: var(--el-text-secondary);
  line-height: 1.6;
  margin-bottom: 10px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 5px;
}

.stat-label { color: var(--el-text-secondary); }
.stat-value { font-weight: 600; }
.val-ok { color: #10b981; }
.val-warn { color: #f59e0b; }
.val-danger { color: #ef4444; }

.option-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.option-label {
  font-size: 12px;
}

.option-label small {
  display: block;
  font-size: 11px;
  color: var(--el-text-secondary);
  margin-top: 1px;
}

/* 日志列表 */
.log-list {
  max-height: 250px;
  overflow-y: auto;
}

.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
  font-size: 12px;
}

.log-content { flex: 1; }
.log-text { color: var(--el-text-regular); line-height: 1.5; }
.log-time { font-size: 10px; color: var(--el-text-secondary); }

/* header */
.header-actions {
  display: flex;
  gap: 8px;
}

.dataset-selector h3 {
  margin-bottom: 12px;
  font-size: 14px;
}
</style>
