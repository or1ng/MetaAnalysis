<template>
  <div>
    <div class="page-header">
      <h2>自动化报告生成</h2>
    </div>

    <div class="report-layout">
      <!-- 左侧：配置面板 -->
      <div class="config-panel page-card">
        <h3>报告配置</h3>
        <el-form label-width="90px" size="default">
          <el-form-item label="数据集">
            <el-select v-model="currentDataset" style="width:100%">
              <el-option v-for="ds in datasetList" :key="ds.id" :label="ds.name" :value="ds.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="报告模板">
            <el-radio-group v-model="template">
              <el-radio value="business">商务汇报</el-radio>
              <el-radio value="academic">学术论文</el-radio>
              <el-radio value="simple">简约分析</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="包含图表">
            <el-switch v-model="includeCharts" />
          </el-form-item>
          <el-form-item label="统计结论">
            <el-switch v-model="includeStats" />
          </el-form-item>
          <el-form-item label="风险建议">
            <el-switch v-model="includeSuggestions" />
          </el-form-item>
          <el-divider />
          <el-button type="primary" size="large" style="width:100%" @click="handleGenerate" :loading="generating">
            <el-icon><Document /></el-icon> 生成报告
          </el-button>
        </el-form>

        <el-divider v-if="reportList.length > 0">历史报告</el-divider>
        <div v-if="reportList.length > 0" class="report-list">
          <div
            v-for="r in reportList" :key="r.id"
            class="report-item"
            :class="{ active: currentReportId === r.id }"
            @click="handlePreview(r)"
          >
            <div class="report-item-title">{{ r.dataset_name }}</div>
            <div class="report-item-time">{{ r.created_at }}</div>
          </div>
        </div>
      </div>

      <!-- 右侧：报告预览 -->
      <div class="preview-panel page-card">
        <div class="preview-toolbar">
          <h3>报告预览</h3>
          <div>
            <el-button size="small" @click="handleDownload" :disabled="!currentReportId">下载HTML</el-button>
            <el-button size="small" type="danger" @click="handleDelete" :disabled="!currentReportId">删除</el-button>
          </div>
        </div>
        <div class="preview-content">
          <div v-if="!currentReportId" class="preview-placeholder">
            <el-icon :size="64" color="#c0c4cc"><Document /></el-icon>
            <p>配置参数后点击"生成报告"</p>
          </div>
          <div v-else class="report-html" :class="'theme-' + currentTemplate" v-html="sanitizedHtml"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { generateReport, getReports, previewReport, downloadReport, deleteReport } from '@/api/report'
import { getDatasets } from '@/api/dataset'

const currentDataset = ref(null)
const datasetList = ref([])
const template = ref('business')
const includeCharts = ref(true)
const includeStats = ref(true)
const includeSuggestions = ref(true)
const generating = ref(false)
const currentReportId = ref(null)
const reportHtml = ref('')
const reportList = ref([])

const templateNames = { business: '商务汇报分析报告', academic: '学术研究报告', simple: '数据简报' }

/**
 * 从完整的报告 HTML 中提取 <body> 内的内容，
 * 并剥离内嵌 <style> 标签，防止样式泄漏到父页面。
 */
function extractBodyContent(html) {
  if (!html) return ''
  // 移除 <style>...</style>
  let cleaned = html.replace(/<style[\s\S]*?<\/style>/gi, '')
  // 提取 <body>...</body> 内容
  const bodyMatch = cleaned.match(/<body[^>]*>([\s\S]*?)<\/body>/i)
  if (bodyMatch) {
    cleaned = bodyMatch[1].trim()
  } else {
    // 没有 body 标签则去掉 html/head
    cleaned = cleaned.replace(/<(!DOCTYPE|html|head)[\s\S]*?>/gi, '')
    cleaned = cleaned.replace(/<\/(html|head|body)>/gi, '')
  }
  return cleaned
}

// 记录当前预览报告的模板类型，用于切换 CSS class
const currentTemplate = ref('business')

const sanitizedHtml = computed(() => extractBodyContent(reportHtml.value))

onMounted(async () => {
  try {
    const res = await getDatasets()
    datasetList.value = res.data?.items || res.data || []
    if (datasetList.value.length > 0) {
      currentDataset.value = datasetList.value[0].id
    }
    await loadReportList()
  } catch (e) {
    console.error('初始化失败', e)
  }
})

async function loadReportList() {
  try {
    const res = await getReports()
    reportList.value = res.data?.items || res.data || []
  } catch (e) {
    console.error('加载报告列表失败', e)
  }
}

async function handleGenerate() {
  if (!currentDataset.value) {
    ElMessage.warning('请先选择数据集')
    return
  }
  generating.value = true
  try {
    const res = await generateReport({
      dataset_id: Number(currentDataset.value),
      template: template.value,
      include_charts: includeCharts.value,
      include_stats: includeStats.value,
      include_suggestions: includeSuggestions.value,
    })
    const reportId = res.data?.report_id
    if (reportId) {
      currentReportId.value = reportId
      ElMessage.success('报告生成成功')
      await handlePreview({ id: reportId, template: template.value })
      await loadReportList()
    }
  } catch (e) {
    ElMessage.error(`生成失败: ${e.message}`)
  } finally {
    generating.value = false
  }
}

async function handlePreview(r) {
  currentReportId.value = r.id
  currentTemplate.value = r.template || 'business'
  try {
    const res = await previewReport(r.id)
    reportHtml.value = res.data?.content_html || res.data?.html || ''
  } catch (e) {
    ElMessage.error('加载报告预览失败')
  }
}

async function handleDownload() {
  if (!currentReportId.value) return
  try {
    const res = await downloadReport(currentReportId.value)
    const blob = res instanceof Blob ? res : new Blob([res], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${currentReportId.value}.html`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (e) {
    ElMessage.error('下载失败')
  }
}

async function handleDelete() {
  if (!currentReportId.value) return
  try {
    await ElMessageBox.confirm('确定删除该报告？', '提示', { type: 'warning' })
    await deleteReport(currentReportId.value)
    currentReportId.value = null
    reportHtml.value = ''
    ElMessage.success('已删除')
    await loadReportList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.report-layout { display: grid; grid-template-columns: 300px 1fr; gap: 16px; height: calc(100vh - 140px); }
.config-panel { overflow-y: auto; }
.preview-panel { display: flex; flex-direction: column; }
.preview-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.preview-content { flex: 1; overflow: auto; border: 1px solid var(--border-color); border-radius: 8px; }
.preview-placeholder {
  height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: #c0c4cc;
}
.report-html { padding: 24px; line-height: 1.8; overflow-x: hidden; }
.report-html :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; table-layout: fixed; }
.report-html :deep(th), .report-html :deep(td) { padding: 8px 12px; text-align: left; font-size: 13px; word-break: break-all; }
.report-html :deep(ul), .report-html :deep(ol) { padding-left: 20px; }
.report-html :deep(li) { margin-bottom: 4px; }

/* ── 商务汇报主题 ── */
.theme-business :deep(h1) { font-size: 22px; color: #2c3e50; margin-bottom: 12px; border-bottom: 3px solid #2980b9; padding-bottom: 8px; }
.theme-business :deep(h2) { font-size: 18px; color: #2980b9; border-left: 4px solid #2980b9; padding-left: 12px; margin: 24px 0 12px; }
.theme-business :deep(h3) { font-size: 16px; color: #34495e; margin: 16px 0 8px; }
.theme-business :deep(th) { background: #3498db; color: #fff; border: 1px solid #ecf0f1; }
.theme-business :deep(td) { border: 1px solid #ecf0f1; }
.theme-business :deep(.kpi-row) { display: flex; gap: 16px; flex-wrap: wrap; margin: 12px 0; }
.theme-business :deep(.kpi-card) { background: linear-gradient(135deg, #2980b9, #3498db); color: #fff; padding: 14px 20px; border-radius: 8px; min-width: 100px; text-align: center; }
.theme-business :deep(.kpi-card .kpi-value) { font-size: 24px; font-weight: 700; }
.theme-business :deep(.kpi-card .kpi-label) { font-size: 11px; opacity: 0.85; }
.theme-business :deep(.kpi-card.green) { background: linear-gradient(135deg, #27ae60, #2ecc71); }
.theme-business :deep(.kpi-card.orange) { background: linear-gradient(135deg, #e67e22, #f39c12); }
.theme-business :deep(.kpi-card.red) { background: linear-gradient(135deg, #c0392b, #e74c3c); }
.theme-business :deep(.rank-bar) { height: 16px; background: linear-gradient(90deg, #3498db, #2980b9); border-radius: 8px; }
.theme-business :deep(.insight) { background: #eaf2f8; border-left: 3px solid #2980b9; padding: 10px 14px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.theme-business :deep(.warning) { background: #fdedec; border-left: 3px solid #e74c3c; padding: 10px 14px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.theme-business :deep(.success) { background: #eafaf1; border-left: 3px solid #27ae60; padding: 10px 14px; margin: 8px 0; border-radius: 0 6px 6px 0; }
.theme-business :deep(.action-item) { background: #fef9e7; border-left: 3px solid #f39c12; padding: 10px 14px; margin: 8px 0; border-radius: 0 6px 6px 0; }

/* ── 学术论文主题 ── */
.theme-academic { font-family: 'Times New Roman', 'SimSun', serif !important; color: #333; }
.theme-academic :deep(h1) { font-size: 20px; color: #1a1a1a; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 6px; }
.theme-academic :deep(h2) { font-size: 17px; color: #333; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin: 24px 0 12px; }
.theme-academic :deep(h3) { font-size: 15px; color: #444; margin: 16px 0 8px; }
.theme-academic :deep(th) { background: #e8e8e8; border: 1px solid #999; font-weight: 600; }
.theme-academic :deep(td) { border: 1px solid #ccc; }
.theme-academic :deep(.note) { background: #f5f5f5; border: 1px solid #ddd; padding: 10px 14px; margin: 10px 0; font-size: 13px; border-radius: 2px; }
.theme-academic :deep(.finding) { background: #fafafa; border-left: 3px solid #666; padding: 10px 14px; margin: 10px 0; font-size: 13px; }
.theme-academic :deep(.sig-high) { color: #c0392b; font-weight: 600; }
.theme-academic :deep(.sig-mid) { color: #e67e22; font-weight: 600; }
.theme-academic :deep(.formula) { font-family: 'Courier New', monospace; background: #f9f9f9; padding: 2px 6px; border-radius: 2px; }

/* ── 简约分析主题 ── */
.theme-simple :deep(h1) { font-size: 20px; color: #2c3e50; margin-bottom: 8px; }
.theme-simple :deep(.section-title) { font-size: 15px; font-weight: 700; color: #2ecc71; margin-bottom: 10px; }
.theme-simple :deep(th) { background: #2ecc71; color: #fff; border-bottom: 1px solid #eee; }
.theme-simple :deep(td) { border-bottom: 1px solid #eee; }
.theme-simple :deep(.stat-grid) { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; margin: 10px 0; }
.theme-simple :deep(.stat-item) { background: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; }
.theme-simple :deep(.stat-item .val) { font-size: 18px; font-weight: 700; color: #2c3e50; }
.theme-simple :deep(.stat-item .lbl) { font-size: 11px; color: #999; }
.theme-simple :deep(.bullet) { padding: 6px 0 6px 16px; position: relative; }
.theme-simple :deep(.bullet::before) { content: ""; position: absolute; left: 0; top: 12px; width: 6px; height: 6px; background: #2ecc71; border-radius: 50%; }
.theme-simple :deep(.tag) { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.theme-simple :deep(.tag-green) { background: #d5f5e3; color: #27ae60; }
.theme-simple :deep(.tag-red) { background: #fadbd8; color: #e74c3c; }

.report-list { max-height: 200px; overflow-y: auto; }
.report-item {
  padding: 10px 12px; background: #f5f7fa; border-radius: 4px;
  margin-bottom: 6px; cursor: pointer; transition: all 0.2s;
}
.report-item:hover { background: #eff6ff; }
.report-item.active { background: var(--primary); color: #fff; }
.report-item-title { font-size: 13px; font-weight: 500; }
.report-item-time { font-size: 11px; color: #909399; margin-top: 2px; }
.report-item.active .report-item-time { color: rgba(255,255,255,0.7); }
</style>
