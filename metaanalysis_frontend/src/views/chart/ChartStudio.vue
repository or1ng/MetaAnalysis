<template>
  <div>
    <div class="page-header">
      <h2>智能可视化</h2>
    </div>

    <div class="chart-layout">
      <!-- 左侧：字段栏 -->
      <div class="field-panel page-card">
        <h3>数据集</h3>
        <el-select v-model="currentDataset" style="width:100%;margin-bottom:12px" @change="onDatasetChange">
          <el-option v-for="ds in datasetList" :key="ds.id" :label="ds.name" :value="ds.id" />
        </el-select>
        <div class="field-section">
          <div class="section-label">维度 / 分类</div>
          <div
            v-for="f in textFields" :key="f"
            :class="['draggable-field', { active: xField === f }]"
            @click="selectXField(f)"
          >{{ f }}</div>
          <div class="section-label" style="margin-top:12px">指标 / 数值</div>
          <div
            v-for="f in numericFields" :key="f"
            :class="['draggable-field metric', { active: yFields.includes(f) }]"
            @click="toggleYField(f)"
          >{{ f }}</div>
          <div v-if="dateFields.length > 0" class="section-label" style="margin-top:12px">日期</div>
          <div
            v-for="f in dateFields" :key="f"
            :class="['draggable-field', { active: xField === f }]"
            @click="selectXField(f)"
          >{{ f }}</div>
        </div>
      </div>

      <!-- 中间：图表画布 -->
      <div class="canvas-panel page-card">
        <div class="chart-toolbar">
          <div class="chart-type-selector">
            <el-radio-group v-model="chartType" size="small">
              <el-radio-button value="bar">柱状图</el-radio-button>
              <el-radio-button value="line">折线图</el-radio-button>
              <el-radio-button value="area">面积图</el-radio-button>
              <el-radio-button value="pie">饼图</el-radio-button>
              <el-radio-button value="scatter">散点图</el-radio-button>
              <el-radio-button value="boxplot">箱线图</el-radio-button>
              <el-radio-button value="histogram">直方图</el-radio-button>
            </el-radio-group>
          </div>
          <div>
            <el-button type="primary" size="small" @click="handleGenerate" :loading="loading">生成图表</el-button>
            <el-button size="small" @click="handleBatch" :loading="batchLoading">自动出图</el-button>
            <el-button size="small" @click="handleExportPNG" :disabled="!chartGenerated">导出PNG</el-button>
          </div>
        </div>
        <div class="chart-canvas" ref="chartCanvas">
          <div v-show="chartGenerated" ref="echartRef" style="width:100%;height:100%"></div>
          <div v-if="!chartGenerated" class="chart-placeholder">
            <el-icon :size="64" color="#c0c4cc"><PieChart /></el-icon>
            <p>选择数据集和字段后生成图表</p>
          </div>
        </div>

        <!-- 批量图表网格 -->
        <div v-if="batchResults.length > 0" class="batch-grid">
          <div
            v-for="(item, idx) in batchResults" :key="idx"
            class="batch-chart-card"
            :class="{ active: activeBatchIdx === idx }"
            @click="showBatchChart(idx)"
          >
            <div class="batch-chart-title">{{ item.title || item.chart_type }}</div>
            <div :ref="el => { if (el) batchRefs[idx] = el }" class="batch-chart-inner"></div>
          </div>
        </div>
      </div>

      <!-- 右侧：样式配置 -->
      <div class="style-panel page-card">
        <h3>样式配置</h3>
        <el-form label-width="70px" size="small">
          <el-form-item label="配色方案">
            <el-select v-model="colorScheme" style="width:100%">
              <el-option label="默认蓝" value="default" />
              <el-option label="商务绿" value="green" />
              <el-option label="科技紫" value="purple" />
            </el-select>
          </el-form-item>
          <el-form-item label="图表标题">
            <el-input v-model="chartTitle" placeholder="留空自动生成" />
          </el-form-item>
          <el-form-item label="图例">
            <el-switch v-model="showLegend" />
          </el-form-item>
        </el-form>
        <el-divider v-if="batchResults.length > 0">批量图表</el-divider>
        <div v-if="batchResults.length > 0" class="batch-list">
          <div
            v-for="(item, idx) in batchResults" :key="idx"
            class="batch-item"
            :class="{ active: activeBatchIdx === idx }"
            @click="showBatchChart(idx)"
          >
            {{ item.title || item.chart_type }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { generateChart, getChartFields, batchCharts } from '@/api/chart'
import { getDatasets } from '@/api/dataset'

const currentDataset = ref(null)
const datasetList = ref([])
const textFields = ref([])
const numericFields = ref([])
const dateFields = ref([])
const xField = ref(null)
const yFields = ref([])
const chartType = ref('bar')
const colorScheme = ref('default')
const chartTitle = ref('')
const showLegend = ref(true)
const loading = ref(false)
const batchLoading = ref(false)
const chartGenerated = ref(false)
const echartRef = ref(null)
const chartCanvas = ref(null)
let chartInstance = null
const batchResults = ref([])
const activeBatchIdx = ref(-1)
const batchRefs = {}
let batchInstances = []

onMounted(async () => {
  try {
    const res = await getDatasets()
    datasetList.value = res.data?.items || res.data || []
    if (datasetList.value.length > 0) {
      currentDataset.value = datasetList.value[0].id
      await onDatasetChange()
    }
  } catch (e) {
    console.error('加载数据集失败', e)
  }
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  batchInstances.forEach(inst => inst?.dispose())
  batchInstances = []
  window.removeEventListener('resize', handleResize)
})

async function onDatasetChange() {
  if (!currentDataset.value) return
  textFields.value = []
  numericFields.value = []
  dateFields.value = []
  xField.value = null
  yFields.value = []
  chartGenerated.value = false
  destroyBatchGrid()
  batchResults.value = []
  try {
    const res = await getChartFields(currentDataset.value)
    const d = res.data || {}
    textFields.value = d.text || []
    numericFields.value = d.numeric || []
    dateFields.value = d.date || []
  } catch (e) {
    console.error('加载字段失败', e)
  }
}

function selectXField(f) {
  xField.value = f
}

function toggleYField(f) {
  const idx = yFields.value.indexOf(f)
  if (idx >= 0) yFields.value.splice(idx, 1)
  else yFields.value.push(f)
}

async function handleGenerate() {
  if (!currentDataset.value) {
    ElMessage.warning('请先选择数据集')
    return
  }
  loading.value = true
  try {
    const payload = {
      dataset_id: Number(currentDataset.value),
      chart_type: chartType.value,
      x_field: xField.value || undefined,
      y_fields: yFields.value.length > 0 ? yFields.value : undefined,
      title: chartTitle.value || '',
      color_scheme: colorScheme.value,
      show_legend: showLegend.value,
    }
    const res = await generateChart(payload)
    const option = res.data?.echarts_option
    if (!option) {
      ElMessage.error(res.data?.message || '生成失败')
      return
    }
    await renderChart(option)
    destroyBatchGrid()
    batchResults.value = []
    activeBatchIdx.value = -1
  } catch (e) {
    ElMessage.error(`生成失败: ${e.message}`)
  } finally {
    loading.value = false
  }
}

async function handleBatch() {
  if (!currentDataset.value) {
    ElMessage.warning('请先选择数据集')
    return
  }
  batchLoading.value = true
  try {
    const res = await batchCharts({
      dataset_id: Number(currentDataset.value),
      chart_type: chartType.value,
    })
    const items = res.data?.charts || []
    if (items.length === 0) {
      ElMessage.info('没有生成任何图表')
      return
    }
    batchResults.value = items
    activeBatchIdx.value = 0
    await renderChart(items[0].echarts_option)
    await nextTick()
    renderBatchGrid()
    ElMessage.success(`已生成 ${items.length} 个图表`)
  } catch (e) {
    ElMessage.error(`批量生成失败: ${e.message}`)
  } finally {
    batchLoading.value = false
  }
}

async function showBatchChart(idx) {
  const item = batchResults.value[idx]
  if (!item?.echarts_option) return
  activeBatchIdx.value = idx
  await renderChart(item.echarts_option)
}

function renderBatchGrid() {
  destroyBatchGrid()
  const items = batchResults.value
  items.forEach((item, idx) => {
    const el = batchRefs[idx]
    if (!el) return
    const inst = echarts.init(el)
    inst.setOption(item.echarts_option)
    batchInstances.push(inst)
  })
}

function destroyBatchGrid() {
  batchInstances.forEach(inst => inst?.dispose())
  batchInstances = []
}

async function renderChart(option) {
  chartGenerated.value = true
  await nextTick()
  if (!echartRef.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(echartRef.value)
  chartInstance.setOption(option)
  window.addEventListener('resize', handleResize)
}

function handleResize() {
  if (chartInstance) chartInstance.resize()
}

function handleExportPNG() {
  if (!chartInstance) return
  const url = chartInstance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' })
  const link = document.createElement('a')
  link.download = `chart_${Date.now()}.png`
  link.href = url
  link.click()
  ElMessage.success('图表已导出')
}
</script>

<style scoped>
.chart-layout { display: grid; grid-template-columns: 160px 1fr 220px; gap: 16px; height: calc(100vh - 140px); }
.field-section { max-height: 100%; overflow-y: auto; }
.section-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; font-weight: 600; }
.draggable-field {
  padding: 6px 10px; margin-bottom: 4px; background: #f5f7fa; border-radius: 4px;
  font-size: 13px; cursor: pointer; color: var(--text-regular);
  transition: all 0.2s;
}
.draggable-field:hover { background: #eff6ff; }
.draggable-field.active { background: var(--primary); color: #fff; }
.draggable-field.metric { background: #eff6ff; color: var(--primary); }
.draggable-field.metric.active { background: var(--primary); color: #fff; }
.canvas-panel { display: flex; flex-direction: column; }
.chart-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.chart-canvas {
  flex: 1; border: 1px dashed var(--border-color); border-radius: 8px;
  display: flex; align-items: center; justify-content: center; min-height: 300px;
  position: relative;
}
.chart-placeholder { text-align: center; color: #c0c4cc; }
.chart-placeholder p { margin-top: 8px; }
.batch-list { max-height: 200px; overflow-y: auto; }
.batch-item {
  padding: 8px 12px; background: #f5f7fa; border-radius: 4px;
  font-size: 13px; margin-bottom: 6px; cursor: pointer; text-align: center;
  transition: all 0.2s;
}
.batch-item:hover { background: #eff6ff; color: var(--primary); }
.batch-item.active { background: var(--primary); color: #fff; }

/* 批量图表网格 */
.batch-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding-top: 12px;
  max-height: calc(100vh - 480px);
  overflow-y: auto;
}
.batch-chart-card {
  background: #fafafa;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.batch-chart-card:hover { border-color: var(--primary); }
.batch-chart-card.active { border-color: var(--primary); border-width: 2px; }
.batch-chart-title {
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}
.batch-chart-inner { width: 100%; height: 200px; }
</style>
