<template>
  <div>
    <div class="page-header">
      <h2>高阶统计分析</h2>
      <div class="header-actions">
        <el-select v-model="currentDatasetId" placeholder="选择数据集" style="width:200px" @change="loadFields">
          <el-option v-for="d in datasetList" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
      </div>
    </div>

    <div class="stat-layout" v-if="currentDatasetId">
      <!-- 左侧：统计功能导航 -->
      <div class="nav-panel page-card">
        <div class="nav-title">统计功能</div>
        <div class="nav-group">
          <div class="nav-group-label">基础统计</div>
          <div class="nav-item" :class="{ active: activeFunc === 'descriptive' }" @click="activeFunc = 'descriptive'">
            <el-icon><DataLine /></el-icon>描述统计
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-label">推断统计</div>
          <div class="nav-item" :class="{ active: activeFunc === 'hypothesis' }" @click="activeFunc = 'hypothesis'">
            <el-icon><Opportunity /></el-icon>假设检验
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-label">关联分析</div>
          <div class="nav-item" :class="{ active: activeFunc === 'correlation' }" @click="activeFunc = 'correlation'">
            <el-icon><Connection /></el-icon>相关分析
          </div>
          <div class="nav-item" :class="{ active: activeFunc === 'regression' }" @click="activeFunc = 'regression'">
            <el-icon><TrendCharts /></el-icon>回归分析
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-label">时序分析</div>
          <div class="nav-item" :class="{ active: activeFunc === 'timeseries' }" @click="activeFunc = 'timeseries'">
            <el-icon><Timer /></el-icon>时序分析
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-label">数据挖掘</div>
          <div class="nav-item" :class="{ active: activeFunc === 'clustering' }" @click="activeFunc = 'clustering'">
            <el-icon><Aim /></el-icon>聚类分析
          </div>
          <div class="nav-item" :class="{ active: activeFunc === 'dbscan' }" @click="activeFunc = 'dbscan'">
            <el-icon><Histogram /></el-icon>DBSCAN聚类
          </div>
        </div>
        <div class="nav-group">
          <div class="nav-group-label">高级建模</div>
          <div class="nav-item" :class="{ active: activeFunc === 'logistic' }" @click="activeFunc = 'logistic'">
            <el-icon><Odometer /></el-icon>逻辑回归
          </div>
          <div class="nav-item" :class="{ active: activeFunc === 'pca' }" @click="activeFunc = 'pca'">
            <el-icon><Grid /></el-icon>PCA降维
          </div>
          <div class="nav-item" :class="{ active: activeFunc === 'arima' }" @click="activeFunc = 'arima'">
            <el-icon><TrendCharts /></el-icon>ARIMA预测
          </div>
        </div>
      </div>

      <!-- 中间：参数配置面板 -->
      <div class="params-panel">
        <div class="section-title">{{ funcNames[activeFunc] }}</div>

        <!-- ── 描述统计 ── -->
        <template v-if="activeFunc === 'descriptive'">
          <div class="param-card page-card">
            <div class="pc-title">选择分析字段</div>
            <div class="pc-desc">选择一个或多个数值型字段进行描述统计，系统将自动计算均值、标准差、分位数、偏度、峰度等指标及正态性检验。</div>
            <div class="field-selector">
              <div class="fs-label">数值型字段</div>
              <div class="field-tags">
                <div v-for="f in numericFields" :key="f" class="field-tag"
                  :class="{ selected: selectedFields.includes(f) }" @click="toggleField(f)">{{ f }}</div>
              </div>
              <div class="field-actions">
                <el-button size="small" @click="selectedFields = [...numericFields]">全选</el-button>
                <el-button size="small" @click="selectedFields = []">清空</el-button>
              </div>
            </div>
          </div>
          <div class="param-card page-card">
            <div class="pc-title">高级设置</div>
            <el-form label-width="100px" size="default">
              <el-form-item label="置信水平">
                <el-select v-model="params.descriptive.confidence" style="width:200px">
                  <el-option label="90%（α=0.10）" :value="0.90" />
                  <el-option label="95%（α=0.05）" :value="0.95" />
                  <el-option label="99%（α=0.01）" :value="0.99" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── 假设检验 ── -->
        <template v-if="activeFunc === 'hypothesis'">
          <div class="param-card page-card">
            <div class="pc-title">检验方法</div>
            <el-form label-width="120px" size="default">
              <el-form-item label="检验类型">
                <el-select v-model="params.hypothesis.method" style="width:240px">
                  <el-option label="独立样本t检验" value="ttest_independent" />
                  <el-option label="配对样本t检验" value="ttest_paired" />
                  <el-option label="卡方检验" value="chi2_test" />
                  <el-option label="单因素ANOVA" value="anova" />
                  <el-option label="正态性检验" value="normality" />
                </el-select>
              </el-form-item>

              <!-- 独立样本t -->
              <template v-if="params.hypothesis.method === 'ttest_independent'">
                <el-form-item label="分组列">
                  <el-select v-model="params.hypothesis.group_col" placeholder="选择分组列" style="width:240px">
                    <el-option v-for="f in textFields" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
                <el-form-item label="值列">
                  <el-select v-model="params.hypothesis.value_col" placeholder="选择数值列" style="width:240px">
                    <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
                <el-form-item label="比较组A">
                  <el-select v-model="params.hypothesis.group_a" placeholder="组A" style="width:240px" :disabled="!params.hypothesis.group_col">
                    <el-option v-for="g in groupValues" :key="g" :label="g" :value="g" />
                  </el-select>
                </el-form-item>
                <el-form-item label="比较组B">
                  <el-select v-model="params.hypothesis.group_b" placeholder="组B" style="width:240px" :disabled="!params.hypothesis.group_col">
                    <el-option v-for="g in groupValues" :key="g" :label="g" :value="g" />
                  </el-select>
                </el-form-item>
              </template>

              <!-- 配对t -->
              <template v-if="params.hypothesis.method === 'ttest_paired'">
                <el-form-item label="配对列A">
                  <el-select v-model="params.hypothesis.col_a" placeholder="列A" style="width:240px">
                    <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
                <el-form-item label="配对列B">
                  <el-select v-model="params.hypothesis.col_b" placeholder="列B" style="width:240px">
                    <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
              </template>

              <!-- 卡方 -->
              <template v-if="params.hypothesis.method === 'chi2_test'">
                <el-form-item label="列A">
                  <el-select v-model="params.hypothesis.col_a" placeholder="列A" style="width:240px">
                    <el-option v-for="f in textFields" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
                <el-form-item label="列B">
                  <el-select v-model="params.hypothesis.col_b" placeholder="列B" style="width:240px">
                    <el-option v-for="f in textFields" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
              </template>

              <!-- ANOVA -->
              <template v-if="params.hypothesis.method === 'anova'">
                <el-form-item label="分组列">
                  <el-select v-model="params.hypothesis.group_col" placeholder="选择分组列" style="width:240px">
                    <el-option v-for="f in textFields" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
                <el-form-item label="值列">
                  <el-select v-model="params.hypothesis.value_col" placeholder="选择数值列" style="width:240px">
                    <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
              </template>

              <!-- 正态性检验 -->
              <template v-if="params.hypothesis.method === 'normality'">
                <el-form-item label="检验字段">
                  <div class="field-selector" style="width:100%">
                    <div class="field-tags">
                      <div v-for="f in numericFields" :key="f" class="field-tag"
                        :class="{ selected: selectedFields.includes(f) }" @click="toggleField(f)">{{ f }}</div>
                    </div>
                    <div class="field-actions">
                      <el-button size="small" @click="selectedFields = [...numericFields]">全选</el-button>
                      <el-button size="small" @click="selectedFields = []">清空</el-button>
                    </div>
                    <div style="font-size:11px;color:#9ca3af;margin-top:4px">
                      {{ selectedFields.length ? `已选 ${selectedFields.length} 个字段` : '未选择则默认检验全部数值字段' }}
                    </div>
                  </div>
                </el-form-item>
              </template>

              <el-form-item label="显著性水平α">
                <el-select v-model="params.hypothesis.alpha" style="width:200px">
                  <el-option label="0.01（极严格）" :value="0.01" />
                  <el-option label="0.05（标准）" :value="0.05" />
                  <el-option label="0.10（宽松）" :value="0.10" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── 相关分析 ── -->
        <template v-if="activeFunc === 'correlation'">
          <div class="param-card page-card">
            <div class="pc-title">选择分析变量</div>
            <div class="pc-desc">选择两个或多个数值型变量，计算相关系数矩阵和p值。</div>
            <div class="field-selector">
              <div class="fs-label">数值型字段</div>
              <div class="field-tags">
                <div v-for="f in numericFields" :key="f" class="field-tag"
                  :class="{ selected: selectedFields.includes(f) }" @click="toggleField(f)">{{ f }}</div>
              </div>
              <div class="field-actions">
                <el-button size="small" @click="selectedFields = [...numericFields]">全选</el-button>
                <el-button size="small" @click="selectedFields = []">清空</el-button>
              </div>
            </div>
          </div>
          <div class="param-card page-card">
            <div class="pc-title">相关系数类型</div>
            <el-form label-width="120px" size="default">
              <el-form-item label="系数类型">
                <el-radio-group v-model="params.correlation.method">
                  <el-radio value="pearson">Pearson（线性）</el-radio>
                  <el-radio value="spearman">Spearman（秩）</el-radio>
                  <el-radio value="kendall">Kendall（τ）</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── 回归分析 ── -->
        <template v-if="activeFunc === 'regression'">
          <div class="param-card page-card">
            <div class="pc-title">变量设置</div>
            <el-form label-width="100px" size="default">
              <el-form-item label="因变量 (Y)">
                <el-select v-model="params.regression.y_col" placeholder="选择因变量" style="width:240px">
                  <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                </el-select>
              </el-form-item>
              <el-form-item label="自变量 (X)">
                <el-select v-model="params.regression.x_cols" multiple placeholder="选择一个或多个自变量" style="width:240px">
                  <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── 时序分析 ── -->
        <template v-if="activeFunc === 'timeseries'">
          <div class="param-card page-card">
            <div class="pc-title">时序设置</div>
            <el-form label-width="100px" size="default">
              <el-form-item label="时间列">
                <el-select v-model="params.timeseries.date_col" placeholder="选择时间列" style="width:240px">
                  <el-option v-for="f in dateFields" :key="f" :label="f" :value="f" />
                </el-select>
                <div v-if="dateFields.length === 0" style="font-size:11px;color:#f59e0b;margin-top:4px">⚠ 当前数据集未检测到日期/时间字段</div>
              </el-form-item>
              <el-form-item label="值列">
                <el-select v-model="params.timeseries.value_col" placeholder="选择数值列" style="width:240px">
                  <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                </el-select>
              </el-form-item>
              <el-form-item label="预测期数">
                <el-input-number v-model="params.timeseries.periods" :min="1" :max="30" />
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── 聚类分析 ── -->
        <template v-if="activeFunc === 'clustering'">
          <div class="param-card page-card">
            <div class="pc-title">选择聚类字段</div>
            <div class="pc-desc">选择数值型字段作为聚类特征，推荐标准化后进行K-Means聚类。</div>
            <div class="field-selector">
              <div class="fs-label">数值型字段</div>
              <div class="field-tags">
                <div v-for="f in numericFields" :key="f" class="field-tag"
                  :class="{ selected: selectedFields.includes(f) }" @click="toggleField(f)">{{ f }}</div>
              </div>
              <div class="field-actions">
                <el-button size="small" @click="selectedFields = [...numericFields]">全选</el-button>
                <el-button size="small" @click="selectedFields = []">清空</el-button>
              </div>
            </div>
          </div>
          <div class="param-card page-card">
            <div class="pc-title">聚类参数</div>
            <el-form label-width="100px" size="default">
              <el-form-item label="聚类数K">
                <el-input-number v-model="params.clustering.k" :min="2" :max="10" />
              </el-form-item>
              <el-form-item label="标准化">
                <el-switch v-model="params.clustering.standardize" />
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── DBSCAN聚类 ── -->
        <template v-if="activeFunc === 'dbscan'">
          <div class="param-card page-card">
            <div class="pc-title">选择聚类字段</div>
            <div class="pc-desc">DBSCAN基于密度自动发现任意形状簇，无需预设K，能自动识别噪声点。</div>
            <div class="field-selector">
              <div class="fs-label">数值型字段（≥2个）</div>
              <div class="field-tags">
                <div v-for="f in numericFields" :key="f" class="field-tag"
                  :class="{ selected: selectedFields.includes(f) }" @click="toggleField(f)">{{ f }}</div>
              </div>
              <div class="field-actions">
                <el-button size="small" @click="selectedFields = [...numericFields]">全选</el-button>
                <el-button size="small" @click="selectedFields = []">清空</el-button>
              </div>
            </div>
          </div>
          <div class="param-card page-card">
            <div class="pc-title">DBSCAN参数</div>
            <div class="pc-desc">eps：邻域半径（越小=簇越紧密）；min_samples：成为核心点的最少样本数。</div>
            <el-form label-width="120px" size="default">
              <el-form-item label="eps（邻域半径）">
                <el-input-number v-model="params.dbscan.eps" :min="0.01" :max="10" :step="0.1" :precision="2" />
              </el-form-item>
              <el-form-item label="min_samples">
                <el-input-number v-model="params.dbscan.min_samples" :min="2" :max="50" />
              </el-form-item>
              <el-form-item label="标准化">
                <el-switch v-model="params.dbscan.standardize" />
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── 逻辑回归 ── -->
        <template v-if="activeFunc === 'logistic'">
          <div class="param-card page-card">
            <div class="pc-title">变量设置</div>
            <div class="pc-desc">逻辑回归用于二分类预测，因变量需为0/1或两种类别值，自变量自动标准化。</div>
            <el-form label-width="120px" size="default">
              <el-form-item label="因变量 Y（二分类）">
                <el-select v-model="params.logistic.y_col" placeholder="选择分类字段（文本或数值）" style="width:240px">
                  <el-option v-for="f in binaryCandidateFields" :key="f" :label="f" :value="f" />
                </el-select>
                <div style="font-size:11px;color:#9ca3af;margin-top:4px">仅显示文本型和数值型字段（排除日期列）</div>
              </el-form-item>
              <el-form-item label="自变量 X">
                <el-select v-model="params.logistic.x_cols" multiple placeholder="选择自变量（可多选）" style="width:240px">
                  <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
          <div class="param-card page-card">
            <div class="pc-title">训练设置</div>
            <el-form label-width="120px" size="default">
              <el-form-item label="测试集比例">
                <el-select v-model="params.logistic.test_size" style="width:200px">
                  <el-option label="20%（推荐）" :value="0.2" />
                  <el-option label="25%" :value="0.25" />
                  <el-option label="30%" :value="0.3" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── PCA主成分分析 ── -->
        <template v-if="activeFunc === 'pca'">
          <div class="param-card page-card">
            <div class="pc-title">选择分析字段</div>
            <div class="pc-desc">PCA将多个相关变量降维为少数主成分，保留尽可能多的方差信息，消除多重共线性。</div>
            <div class="field-selector">
              <div class="fs-label">数值型字段（≥2个）</div>
              <div class="field-tags">
                <div v-for="f in numericFields" :key="f" class="field-tag"
                  :class="{ selected: selectedFields.includes(f) }" @click="toggleField(f)">{{ f }}</div>
              </div>
              <div class="field-actions">
                <el-button size="small" @click="selectedFields = [...numericFields]">全选</el-button>
                <el-button size="small" @click="selectedFields = []">清空</el-button>
              </div>
            </div>
          </div>
          <div class="param-card page-card">
            <div class="pc-title">PCA参数</div>
            <el-form label-width="130px" size="default">
              <el-form-item label="主成分数">
                <el-radio-group v-model="pcaAutoMode">
                  <el-radio value="auto">自动（按方差阈值）</el-radio>
                  <el-radio value="manual">手动指定</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="方差阈值" v-if="pcaAutoMode === 'auto'">
                <el-select v-model="params.pca.variance_threshold" style="width:200px">
                  <el-option label="80%（宽松）" :value="0.80" />
                  <el-option label="85%（推荐）" :value="0.85" />
                  <el-option label="90%（严格）" :value="0.90" />
                  <el-option label="95%（最严格）" :value="0.95" />
                </el-select>
              </el-form-item>
              <el-form-item label="主成分数" v-if="pcaAutoMode === 'manual'">
                <el-input-number v-model="params.pca.n_components" :min="1" :max="numericFields.length" />
              </el-form-item>
            </el-form>
          </div>
        </template>

        <!-- ── ARIMA时序预测 ── -->
        <template v-if="activeFunc === 'arima'">
          <div class="param-card page-card">
            <div class="pc-title">时序设置</div>
            <div class="pc-desc">ARIMA是经典时序预测模型，支持自动定阶（AIC准则）或手动指定p/d/q参数。</div>
            <el-form label-width="120px" size="default">
              <el-form-item label="时间列">
                <el-select v-model="params.arima.date_col" placeholder="选择时间列" style="width:240px">
                  <el-option v-for="f in dateFields" :key="f" :label="f" :value="f" />
                </el-select>
                <div v-if="dateFields.length === 0" style="font-size:11px;color:#f59e0b;margin-top:4px">⚠ 当前数据集未检测到日期/时间字段</div>
              </el-form-item>
              <el-form-item label="值列">
                <el-select v-model="params.arima.value_col" placeholder="选择数值列" style="width:240px">
                  <el-option v-for="f in numericFields" :key="f" :label="f" :value="f" />
                </el-select>
              </el-form-item>
              <el-form-item label="预测期数">
                <el-input-number v-model="params.arima.periods" :min="1" :max="60" />
              </el-form-item>
            </el-form>
          </div>
          <div class="param-card page-card">
            <div class="pc-title">模型参数</div>
            <el-form label-width="120px" size="default">
              <el-form-item label="定阶方式">
                <el-radio-group v-model="params.arima.auto_order">
                  <el-radio :value="true">自动定阶（AIC，推荐）</el-radio>
                  <el-radio :value="false">手动指定</el-radio>
                </el-radio-group>
              </el-form-item>
              <template v-if="!params.arima.auto_order">
                <el-form-item label="p（AR阶）">
                  <el-input-number v-model="params.arima.p" :min="0" :max="5" />
                </el-form-item>
                <el-form-item label="d（差分阶）">
                  <el-input-number v-model="params.arima.d" :min="0" :max="2" />
                </el-form-item>
                <el-form-item label="q（MA阶）">
                  <el-input-number v-model="params.arima.q" :min="0" :max="5" />
                </el-form-item>
              </template>
            </el-form>
          </div>
        </template>

        <!-- 运行按钮 -->
        <div class="run-area">
          <el-button type="primary" size="large" @click="handleRun" :loading="running" :disabled="!canRun" style="width:100%">
            <el-icon><VideoPlay /></el-icon> 执行分析
          </el-button>
        </div>
      </div>

      <!-- 右侧：结果面板 -->
      <div class="result-panel page-card">
        <div class="result-header">
          <span class="result-title">分析结果</span>
          <div v-if="hasResult">
            <el-button size="small" @click="exportResult">导出结果</el-button>
          </div>
        </div>
        <div class="result-body">
          <el-empty v-if="!hasResult && !running" description="配置参数后执行分析" :image-size="60" />
          <div v-if="running" style="text-align:center;padding:60px 0">
            <el-icon class="is-loading" :size="32" color="#3a6fd8"><Loading /></el-icon>
            <p style="margin-top:12px;color:#6b7280">分析计算中...</p>
          </div>

          <div v-if="hasResult" class="result-content">

            <!-- 描述统计结果 -->
            <template v-if="activeFunc === 'descriptive' && result">
              <div class="result-section">
                <div class="rs-title">基础统计指标 · {{ result.summary_table?.length || 0 }}个字段</div>
                <el-table :data="result.summary_table" stripe size="small" border>
                  <el-table-column prop="field" label="字段" fixed width="110" />
                  <el-table-column prop="n" label="N" width="55" />
                  <el-table-column prop="mean" label="均值" width="90" />
                  <el-table-column prop="median" label="中位数" width="80" />
                  <el-table-column prop="std" label="标准差" width="80" />
                  <el-table-column prop="min" label="最小" width="80" />
                  <el-table-column prop="max" label="最大" width="80" />
                  <el-table-column prop="q1" label="Q1" width="75" />
                  <el-table-column prop="q3" label="Q3" width="75" />
                  <el-table-column prop="skew" label="偏度" width="70">
                    <template #default="{ row }">
                      <span :style="{ color: Math.abs(row.skew) > 1 ? '#ef4444' : Math.abs(row.skew) > 0.5 ? '#f59e0b' : '' }">{{ row.skew }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="kurtosis" label="峰度" width="70">
                    <template #default="{ row }">
                      <span :style="{ color: row.kurtosis > 3 ? '#ef4444' : '' }">{{ row.kurtosis }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="cv_percent" label="CV%" width="65" />
                  <el-table-column label="95%CI" width="150">
                    <template #default="{ row }">
                      [{{ row.ci_low }}, {{ row.ci_high }}]
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="result-section" v-if="result.normality_test?.length">
                <div class="rs-title">正态性检验</div>
                <el-table :data="result.normality_test" stripe size="small" border>
                  <el-table-column prop="field" label="字段" />
                  <el-table-column prop="test" label="检验方法" width="140" />
                  <el-table-column prop="statistic" label="统计量" width="80" />
                  <el-table-column prop="p_value" label="p值" width="80">
                    <template #default="{ row }">
                      <span :style="{ color: row.p_value && row.p_value < 0.05 ? '#ef4444' : '#10b981', fontWeight: 600 }">
                        {{ row.p_value || '-' }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="结论" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.is_normal ? 'success' : 'danger'" size="small">{{ row.is_normal ? '正态' : '非正态' }}</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- 假设检验结果 -->
            <template v-if="activeFunc === 'hypothesis' && result">
              <div class="result-section">
                <div class="rs-title">{{ result.method || '假设检验结果' }}</div>
                <div v-if="result.results?.length">
                  <div v-for="(r, i) in result.results" :key="i" class="hyp-result">
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item v-for="(val, key) in r" :key="key" :label="key">{{ val }}</el-descriptions-item>
                    </el-descriptions>
                  </div>
                </div>
              </div>
              <div class="result-section" v-if="result.results?.[0]?.posthoc?.length">
                <div class="rs-title">事后检验 (Tukey HSD)</div>
                <el-table :data="result.results[0].posthoc" stripe size="small" border>
                  <el-table-column prop="group_a" label="组A" />
                  <el-table-column prop="group_b" label="组B" />
                  <el-table-column prop="meandiff" label="均值差" width="90" />
                  <el-table-column prop="p_adj" label="p(校正)" width="90" />
                  <el-table-column label="显著" width="70">
                    <template #default="{ row }">
                      <el-tag :type="row.reject ? 'danger' : 'info'" size="small">{{ row.reject ? '显著' : '不显著' }}</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- 相关分析结果 -->
            <template v-if="activeFunc === 'correlation' && result">
              <div class="result-section">
                <div class="rs-title">{{ result.method }}相关矩阵</div>
                <div class="corr-matrix" v-if="result.matrix?.length">
                  <table class="corr-table">
                    <thead>
                      <tr>
                        <th></th>
                        <th v-for="c in result.columns" :key="c">{{ c }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="row in result.matrix" :key="row.col">
                        <th>{{ row.col }}</th>
                        <td v-for="cell in row.values" :key="cell.col"
                          :style="getCorrStyle(cell.r)">
                          <span>{{ cell.r ?? '-' }}</span>
                          <span v-if="cell.sig" style="font-size:9px">✱</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </template>

            <!-- 回归分析结果 -->
            <template v-if="activeFunc === 'regression' && result">
              <div class="result-section">
                <div class="rs-title">回归方程</div>
                <div class="eq-box">{{ result.equation }}</div>
                <div class="metrics-grid">
                  <div class="metric-box">
                    <div class="mb-label">R²</div>
                    <div class="mb-val">{{ result.r_squared }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">调整R²</div>
                    <div class="mb-val">{{ result.adj_r_squared }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">RMSE</div>
                    <div class="mb-val">{{ result.rmse }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">F统计量</div>
                    <div class="mb-val">{{ result.f_statistic }}</div>
                  </div>
                </div>
              </div>
              <div class="result-section">
                <div class="rs-title">系数表</div>
                <el-table :data="result.coefficients" stripe size="small" border>
                  <el-table-column prop="variable" label="变量" width="120" />
                  <el-table-column prop="coefficient" label="系数" width="90" />
                  <el-table-column prop="std_error" label="标准误" width="80" />
                  <el-table-column prop="t_value" label="t值" width="80" />
                  <el-table-column prop="p_value" label="p值" width="80">
                    <template #default="{ row }">
                      <span :style="{ color: row.p_value && row.p_value < 0.05 ? '#ef4444' : '', fontWeight: 600 }">
                        {{ row.p_value ?? '-' }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="beta_std" label="标准化β" width="80" />
                  <el-table-column label="显著性" width="70">
                    <template #default="{ row }">
                      <el-tag :type="row.significant ? 'danger' : 'info'" size="small">{{ row.significant ? '✱' : 'ns' }}</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="result-section" v-if="result.vif?.length">
                <div class="rs-title">多重共线性检测 (VIF)</div>
                <div class="pc-desc" style="margin-bottom:8px">VIF>10提示严重共线性，VIF>5需关注。共线性过高会导致系数不稳定、标准误膨胀。</div>
                <el-table :data="result.vif" stripe size="small" border>
                  <el-table-column prop="variable" label="自变量" width="120" />
                  <el-table-column prop="vif" label="VIF" width="80">
                    <template #default="{ row }">
                      <span :style="{ color: row.vif > 10 ? '#ef4444' : row.vif > 5 ? '#f59e0b' : '', fontWeight: 600 }">
                        {{ row.vif ?? '-' }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="判断" width="120">
                    <template #default="{ row }">
                      <el-tag v-if="row.vif > 10" type="danger" size="small">严重共线性</el-tag>
                      <el-tag v-else-if="row.vif > 5" type="warning" size="small">中度共线性</el-tag>
                      <el-tag v-else type="success" size="small">良好</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- 时序分析结果 -->
            <template v-if="activeFunc === 'timeseries' && result">
              <div class="result-section">
                <div class="rs-title">时序统计摘要</div>
                <el-descriptions :column="3" border size="small">
                  <el-descriptions-item v-for="(val, key) in result.stats" :key="key" :label="key">{{ val }}</el-descriptions-item>
                </el-descriptions>
              </div>
              <div class="result-section" v-if="result.predictions?.length">
                <div class="rs-title">预测值</div>
                <el-table :data="result.predictions" stripe size="small" border>
                  <el-table-column prop="date" label="日期" />
                  <el-table-column prop="predicted" label="预测值" />
                </el-table>
              </div>
            </template>

            <!-- 聚类分析结果 -->
            <template v-if="activeFunc === 'clustering' && result">
              <div class="result-section">
                <div class="rs-title">聚类概况</div>
                <div class="metrics-grid">
                  <div class="metric-box">
                    <div class="mb-label">簇数K</div>
                    <div class="mb-val">{{ result.k }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">样本量</div>
                    <div class="mb-val">{{ result.n }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">轮廓系数</div>
                    <div class="mb-val">{{ result.silhouette_score }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">SSE</div>
                    <div class="mb-val">{{ result.sse }}</div>
                  </div>
                </div>
              </div>
              <div class="result-section" v-if="result.elbow_data?.length">
                <div class="rs-title">肘部法则（Elbow Method）</div>
                <div class="pc-desc" style="margin-bottom:8px">SSE随K变化的趋势，SSE下降速率明显放缓的拐点即为建议的K值。</div>
                <el-table :data="result.elbow_data" stripe size="small" border>
                  <el-table-column prop="k" label="K" width="60" />
                  <el-table-column prop="sse" label="SSE" width="120" />
                  <el-table-column label="SSE下降量" width="120">
                    <template #default="{ row, $index }">
                      <span v-if="$index === 0">-</span>
                      <span v-else>{{ (result.elbow_data[$index - 1].sse - row.sse).toFixed(2) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="SSE分布" min-width="120">
                    <template #default="{ row }">
                      <div class="elbow-bar-wrap">
                        <div class="elbow-bar"
                          :style="{ width: getElbowBarWidth(row.sse, result.elbow_data) + '%', background: row.k === result.k ? '#3a6fd8' : '#c7d2fe' }">
                        </div>
                        <span class="elbow-bar-label" v-if="row.k === result.k">当前</span>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="result-section" v-if="result.cluster_stats?.length">
                <div class="rs-title">各簇统计</div>
                <el-table :data="result.cluster_stats" stripe size="small" border>
                  <el-table-column prop="cluster" label="簇" width="55" />
                  <el-table-column prop="n" label="样本数" width="70" />
                  <el-table-column prop="percentage" label="占比%" width="70" />
                  <el-table-column v-for="f in result.features" :key="f" :label="f + '_均值'" :prop="f + '_mean'" width="90" />
                  <el-table-column v-for="f in result.features" :key="f+'s'" :label="f + '_标准差'" :prop="f + '_std'" width="90" />
                </el-table>
              </div>
            </template>

            <!-- DBSCAN结果 -->
            <template v-if="activeFunc === 'dbscan' && result">
              <div class="result-section">
                <div class="rs-title">DBSCAN概况</div>
                <div class="metrics-grid">
                  <div class="metric-box">
                    <div class="mb-label">有效簇数</div>
                    <div class="mb-val">{{ result.n_clusters }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">噪声点数</div>
                    <div class="mb-val" :style="{ color: result.n_noise > 0 ? '#f59e0b' : '' }">{{ result.n_noise }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">样本总量</div>
                    <div class="mb-val">{{ result.n }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">轮廓系数</div>
                    <div class="mb-val">{{ result.silhouette_score ?? '-' }}</div>
                  </div>
                </div>
              </div>
              <div class="result-section" v-if="result.cluster_stats?.length">
                <div class="rs-title">各簇/噪声点统计</div>
                <el-table :data="result.cluster_stats" stripe size="small" border>
                  <el-table-column prop="label" label="分组" width="80" />
                  <el-table-column prop="n" label="样本数" width="70" />
                  <el-table-column prop="percentage" label="占比%" width="70" />
                  <el-table-column v-for="f in result.features" :key="f" :label="f + '_均值'" :prop="f + '_mean'" width="90">
                    <template #default="{ row }">{{ row.is_noise ? '-' : row[f + '_mean'] }}</template>
                  </el-table-column>
                  <el-table-column label="类型" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.is_noise ? 'warning' : 'primary'" size="small">{{ row.is_noise ? '噪声' : '簇' }}</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="result-section" v-if="result.kdist_sample?.length">
                <div class="rs-title">k-距离图（eps选取参考）</div>
                <div class="pc-desc" style="margin-bottom:8px">k-NN距离排序图中，「肘部」处对应的距离即为建议的eps值。</div>
                <el-table :data="result.kdist_sample.slice(0,20)" stripe size="small" border>
                  <el-table-column prop="idx" label="样本序号" width="90" />
                  <el-table-column prop="dist" label="k-NN距离" width="120" />
                </el-table>
              </div>
            </template>

            <!-- 逻辑回归结果 -->
            <template v-if="activeFunc === 'logistic' && result">
              <div class="result-section">
                <div class="rs-title">模型评估</div>
                <div class="metrics-grid">
                  <div class="metric-box">
                    <div class="mb-label">准确率</div>
                    <div class="mb-val" :style="{ color: result.accuracy >= 0.8 ? '#10b981' : '#f59e0b' }">{{ result.accuracy }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">AUC-ROC</div>
                    <div class="mb-val" :style="{ color: result.auc_roc >= 0.8 ? '#10b981' : result.auc_roc >= 0.7 ? '#f59e0b' : '#ef4444' }">{{ result.auc_roc }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">训练集</div>
                    <div class="mb-val">{{ result.n_train }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">测试集</div>
                    <div class="mb-val">{{ result.n_test }}</div>
                  </div>
                </div>
              </div>
              <div class="result-section" v-if="result.classification_report?.length">
                <div class="rs-title">分类报告</div>
                <el-table :data="result.classification_report" stripe size="small" border>
                  <el-table-column prop="class" label="类别" width="100" />
                  <el-table-column prop="precision" label="精确率" width="80" />
                  <el-table-column prop="recall" label="召回率" width="80" />
                  <el-table-column prop="f1" label="F1分数" width="80">
                    <template #default="{ row }">
                      <span :style="{ color: row.f1 >= 0.8 ? '#10b981' : row.f1 >= 0.6 ? '#f59e0b' : '#ef4444', fontWeight: 600 }">{{ row.f1 }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="support" label="样本数" width="70" />
                </el-table>
              </div>
              <div class="result-section" v-if="result.confusion_matrix">
                <div class="rs-title">混淆矩阵</div>
                <div class="cm-grid">
                  <div class="cm-cell cm-header"></div>
                  <div class="cm-cell cm-header" v-for="cls in result.class_names" :key="cls">预测: {{ cls }}</div>
                  <template v-for="(row, i) in result.confusion_matrix.matrix" :key="i">
                    <div class="cm-cell cm-header">实际: {{ result.class_names[i] }}</div>
                    <div v-for="(val, j) in row" :key="j" class="cm-cell"
                      :class="{ 'cm-tp': i === j, 'cm-fp': i !== j }">{{ val }}</div>
                  </template>
                </div>
              </div>
              <div class="result-section" v-if="result.coefficients?.length">
                <div class="rs-title">系数表（对数几率）</div>
                <el-table :data="result.coefficients" stripe size="small" border>
                  <el-table-column prop="variable" label="变量" />
                  <el-table-column prop="coefficient" label="系数（Log-Odds）" width="140" />
                  <el-table-column prop="odds_ratio" label="Odds Ratio" width="120">
                    <template #default="{ row }">
                      <span :style="{ color: row.odds_ratio > 1 ? '#10b981' : '#ef4444', fontWeight: 600 }">{{ row.odds_ratio }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="影响方向" width="90">
                    <template #default="{ row }">
                      <el-tag :type="row.odds_ratio > 1 ? 'success' : 'danger'" size="small">{{ row.odds_ratio > 1 ? '正向↑' : '负向↓' }}</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- PCA结果 -->
            <template v-if="activeFunc === 'pca' && result">
              <div class="result-section">
                <div class="rs-title">降维概况</div>
                <div class="metrics-grid">
                  <div class="metric-box">
                    <div class="mb-label">原始变量数</div>
                    <div class="mb-val">{{ result.n_original }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">保留主成分数</div>
                    <div class="mb-val">{{ result.n_components }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">方差解释率</div>
                    <div class="mb-val" :style="{ color: '#10b981' }">{{ result.total_variance_explained }}%</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">降维比例</div>
                    <div class="mb-val">{{ ((1 - result.n_components / result.n_original) * 100).toFixed(0) }}%</div>
                  </div>
                </div>
              </div>
              <div class="result-section" v-if="result.variance_table?.length">
                <div class="rs-title">方差解释表</div>
                <el-table :data="result.variance_table" stripe size="small" border>
                  <el-table-column prop="pc" label="主成分" width="80" />
                  <el-table-column prop="eigenvalue" label="特征值" width="90" />
                  <el-table-column prop="variance_ratio" label="贡献率%" width="90">
                    <template #default="{ row }">
                      <span style="font-weight:600;color:#3a6fd8">{{ row.variance_ratio }}%</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="cumulative_ratio" label="累积贡献率%" width="110">
                    <template #default="{ row }">
                      <span :style="{ color: row.cumulative_ratio >= 85 ? '#10b981' : '#6b7280', fontWeight: 600 }">{{ row.cumulative_ratio }}%</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="贡献率分布" min-width="120">
                    <template #default="{ row }">
                      <div class="elbow-bar-wrap">
                        <div class="elbow-bar" :style="{ width: row.variance_ratio + '%', background: '#3a6fd8', maxWidth: '100%' }"></div>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="result-section" v-if="result.loadings?.length">
                <div class="rs-title">载荷矩阵（各变量对主成分的贡献）</div>
                <div class="pc-desc" style="margin-bottom:8px">绝对值越大，表示该变量对主成分贡献越大。</div>
                <el-table :data="result.loadings" stripe size="small" border>
                  <el-table-column prop="pc" label="主成分" width="80" fixed />
                  <el-table-column v-for="col in result.columns" :key="col" :label="col" :prop="col" width="90">
                    <template #default="{ row }">
                      <span :style="{ color: Math.abs(row[col] || 0) >= 0.5 ? '#3a6fd8' : '', fontWeight: Math.abs(row[col] || 0) >= 0.5 ? 600 : 400 }">
                        {{ row[col] }}
                      </span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- ARIMA结果 -->
            <template v-if="activeFunc === 'arima' && result">
              <div class="result-section">
                <div class="rs-title">模型信息</div>
                <div class="metrics-grid">
                  <div class="metric-box">
                    <div class="mb-label">最优阶次</div>
                    <div class="mb-val">ARIMA({{ result.best_order?.p }},{{ result.best_order?.d }},{{ result.best_order?.q }})</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">AIC</div>
                    <div class="mb-val">{{ result.aic }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">MAE</div>
                    <div class="mb-val">{{ result.mae }}</div>
                  </div>
                  <div class="metric-box">
                    <div class="mb-label">RMSE</div>
                    <div class="mb-val">{{ result.rmse }}</div>
                  </div>
                </div>
                <div class="stat-badge-row">
                  <el-tag :type="result.is_stationary ? 'success' : 'warning'" size="small">
                    ADF检验: {{ result.is_stationary ? '序列平稳' : '序列非平稳（已差分）' }}（p={{ result.adf_pvalue }}）
                  </el-tag>
                </div>
              </div>
              <div class="result-section" v-if="result.order_search?.length">
                <div class="rs-title">自动定阶结果（Top 10 AIC）</div>
                <el-table :data="result.order_search" stripe size="small" border>
                  <el-table-column label="阶次 (p,d,q)" width="120">
                    <template #default="{ row }">
                      <span :style="{ fontWeight: row.p === result.best_order?.p && row.d === result.best_order?.d && row.q === result.best_order?.q ? 700 : 400, color: row.p === result.best_order?.p && row.d === result.best_order?.d && row.q === result.best_order?.q ? '#3a6fd8' : '' }">
                        ({{ row.p }},{{ row.d }},{{ row.q }})
                      </span>
                      <el-tag v-if="row.p === result.best_order?.p && row.d === result.best_order?.d && row.q === result.best_order?.q" type="success" size="small" style="margin-left:4px">最优</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="aic" label="AIC" width="100" />
                </el-table>
              </div>
              <div class="result-section" v-if="result.predictions?.length">
                <div class="rs-title">未来{{ result.predictions.length }}期预测（含95%置信区间）</div>
                <el-table :data="result.predictions" stripe size="small" border>
                  <el-table-column prop="date" label="日期" width="110" />
                  <el-table-column prop="predicted" label="预测值" width="100">
                    <template #default="{ row }">
                      <span style="font-weight:600;color:#3a6fd8">{{ row.predicted }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="95%置信区间" min-width="140">
                    <template #default="{ row }">
                      [{{ row.lower_95 }}, {{ row.upper_95 }}]
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- AI解读 -->
            <div class="result-section" v-if="result?.interpretation">
              <div class="rs-title">统计解读</div>
              <div class="interpretation-box">
                <div class="interp-title">📊 自动解读</div>
                <div style="white-space:pre-wrap;line-height:1.8">{{ result.interpretation }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 未选择数据集 -->
    <div v-else class="empty-state">
      <el-empty description="请先选择一个数据集" :image-size="100" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getDatasets } from '@/api/dataset'
import * as statApi from '@/api/statistic'

const activeFunc = ref('descriptive')
const running = ref(false)
const hasResult = ref(false)
const result = ref(null)
const currentDatasetId = ref(null)
const datasetList = ref([])
const numericFields = ref([])
const textFields = ref([])
const dateFields = ref([])
const allFields = ref([])
const selectedFields = ref([])
const groupValues = ref([])

const funcNames = {
  descriptive: '描述统计', hypothesis: '假设检验', correlation: '相关分析',
  regression: '回归分析', timeseries: '时序分析', clustering: '聚类分析',
  dbscan: 'DBSCAN密度聚类', logistic: '逻辑回归', pca: 'PCA主成分分析', arima: 'ARIMA时序预测',
}

// PCA模式：auto / manual
const pcaAutoMode = ref('auto')

const params = reactive({
  descriptive: { confidence: 0.95 },
  hypothesis: { method: 'ttest_independent', alpha: 0.05, group_col: '', value_col: '', group_a: '', group_b: '', col_a: '', col_b: '' },
  correlation: { method: 'pearson' },
  regression: { y_col: '', x_cols: [] },
  timeseries: { date_col: '', value_col: '', periods: 5 },
  clustering: { k: 3, standardize: true },
  dbscan: { eps: 0.5, min_samples: 5, standardize: true },
  logistic: { y_col: '', x_cols: [], test_size: 0.2, random_state: 42 },
  pca: { n_components: null, variance_threshold: 0.85 },
  arima: { date_col: '', value_col: '', periods: 10, auto_order: true, p: 1, d: 1, q: 1 },
})

const canRun = computed(() => {
  if (!currentDatasetId.value) return false
  const needFields = ['descriptive', 'correlation', 'clustering', 'dbscan', 'pca']
  if (needFields.includes(activeFunc.value)) {
    return selectedFields.value.length >= 2 || (activeFunc.value === 'descriptive' && selectedFields.value.length > 0)
  }
  if (activeFunc.value === 'regression') return params.regression.y_col && params.regression.x_cols.length > 0
  if (activeFunc.value === 'timeseries') return params.timeseries.date_col && params.timeseries.value_col
  if (activeFunc.value === 'logistic') return params.logistic.y_col && params.logistic.x_cols.length > 0
  if (activeFunc.value === 'arima') return params.arima.date_col && params.arima.value_col
  return true
})

// 二分类候选字段（文本+数值，排除日期型——日期不适合做分类标签）
const binaryCandidateFields = computed(() => [...textFields.value, ...numericFields.value])

function toggleField(f) {
  const idx = selectedFields.value.indexOf(f)
  if (idx >= 0) selectedFields.value.splice(idx, 1)
  else selectedFields.value.push(f)
}

async function loadDatasets() {
  try {
    const res = await getDatasets()
    if (res.data) {
      const list = res.data.items || res.data
      datasetList.value = Array.isArray(list) ? list : []
    }
    if (datasetList.value.length > 0 && !currentDatasetId.value) {
      currentDatasetId.value = datasetList.value[0].id
      loadFields()
    }
  } catch { /* ignore */ }
}

async function loadFields() {
  if (!currentDatasetId.value) return
  try {
    const res = await statApi.getFields(currentDatasetId.value)
    if (res.data) {
      const d = res.data
      numericFields.value = d.numeric || []
      textFields.value = d.text || []
      dateFields.value = d.date || []
      allFields.value = d.all?.map(f => f.name) || []
      selectedFields.value = []
      result.value = null
      hasResult.value = false
    }
  } catch { /* ignore */ }
}

// 加载分组值
watch(() => params.hypothesis.group_col, async (col) => {
  if (!col || !currentDatasetId.value) { groupValues.value = []; return }
  try {
    const res = await statApi.getColumnValues(currentDatasetId.value, col)
    groupValues.value = res.data || []
    params.hypothesis.group_a = ''
    params.hypothesis.group_b = ''
  } catch { groupValues.value = [] }
})

async function handleRun() {
  if (!canRun.value) return
  running.value = true
  hasResult.value = false
  result.value = null

  try {
    let res
    switch (activeFunc.value) {
      case 'descriptive':
        res = await statApi.descriptive({ dataset_id: currentDatasetId.value, columns: selectedFields.value, ...params.descriptive })
        break
      case 'hypothesis': {
        const p = { dataset_id: currentDatasetId.value, columns: selectedFields.value, ...params.hypothesis }
        res = await statApi.hypothesis(p)
        break
      }
      case 'correlation':
        res = await statApi.correlation({ dataset_id: currentDatasetId.value, columns: selectedFields.value, ...params.correlation })
        break
      case 'regression':
        res = await statApi.regression({ dataset_id: currentDatasetId.value, ...params.regression })
        break
      case 'timeseries':
        res = await statApi.timeseries({ dataset_id: currentDatasetId.value, ...params.timeseries })
        break
      case 'clustering':
        res = await statApi.clustering({ dataset_id: currentDatasetId.value, columns: selectedFields.value, ...params.clustering })
        break
      case 'dbscan':
        res = await statApi.dbscan({ dataset_id: currentDatasetId.value, columns: selectedFields.value, ...params.dbscan })
        break
      case 'logistic':
        res = await statApi.logistic({ dataset_id: currentDatasetId.value, ...params.logistic })
        break
      case 'pca': {
        const pcaP = {
          dataset_id: currentDatasetId.value,
          columns: selectedFields.value,
          variance_threshold: params.pca.variance_threshold,
          n_components: pcaAutoMode.value === 'manual' ? params.pca.n_components : null,
        }
        res = await statApi.pca(pcaP)
        break
      }
      case 'arima':
        res = await statApi.arima({ dataset_id: currentDatasetId.value, ...params.arima })
        break
    }

    if (res.code === 200) {
      result.value = res.data
      hasResult.value = true
      ElMessage.success('分析完成')
    } else {
      ElMessage.error(res.message || '分析失败')
    }
  } catch (e) {
    ElMessage.error('请求失败：' + (e.message || '网络错误'))
  } finally {
    running.value = false
  }
}

function getCorrStyle(r) {
  if (r == null) return { background: '#f3f4f6' }
  const abs = Math.abs(r)
  if (abs >= 0.8) return { background: r > 0 ? '#dcfce7' : '#fef2f2', fontWeight: 700 }
  if (abs >= 0.5) return { background: r > 0 ? '#f0fdf4' : '#fff7ed', fontWeight: 600 }
  if (abs >= 0.3) return { background: r > 0 ? '#f7fef9' : '#fffbf5' }
  return {}
}

function getElbowBarWidth(sse, elbowData) {
  if (!elbowData || !elbowData.length) return 0
  const maxSse = Math.max(...elbowData.map(d => d.sse || 0))
  return maxSse > 0 ? (sse / maxSse) * 100 : 0
}

function exportResult() {
  if (!result.value) return
  const blob = new Blob([JSON.stringify(result.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `statistic_${activeFunc.value}_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出JSON')
}

onMounted(() => { loadDatasets() })
</script>

<style scoped>
.stat-layout {
  display: grid;
  grid-template-columns: 180px 340px 1fr;
  gap: 16px;
  height: calc(100vh - 140px);
  overflow: hidden;
}

.nav-panel {
  overflow-y: auto;
  padding: 0;
}
.nav-title {
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid #e8eaed;
}
.nav-group-label {
  padding: 6px 16px 4px;
  font-size: 11px;
  color: #9ca3af;
  font-weight: 500;
  letter-spacing: 0.04em;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
}
.nav-item:hover { background: #eef2fc; color: #3a6fd8; }
.nav-item.active { background: #eef2fc; color: #3a6fd8; font-weight: 600; border-right: 2px solid #3a6fd8; }

.params-panel {
  overflow-y: auto;
  padding: 20px;
  background: #f0f2f5;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title::before { content: ''; width: 3px; height: 16px; background: #3a6fd8; border-radius: 2px; }

.param-card {
  padding: 16px 18px;
  margin-bottom: 14px;
}
.pc-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.pc-desc { font-size: 12px; color: #9ca3af; margin-bottom: 10px; line-height: 1.6; }

.field-selector { margin-bottom: 8px; }
.fs-label { font-size: 12px; font-weight: 500; color: #6b7280; margin-bottom: 6px; }
.field-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.field-tag {
  background: #f3f4f6; border: 1px solid #e8eaed; border-radius: 4px;
  padding: 4px 10px; font-size: 12px; color: #6b7280; cursor: pointer; transition: all 0.15s;
}
.field-tag.selected { background: #eef2fc; border-color: #3a6fd8; color: #3a6fd8; font-weight: 500; }
.field-tag:hover { background: #eef2fc; color: #3a6fd8; }
.field-actions { margin-top: 4px; }

.run-area { margin-top: 16px; }

.result-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid #e8eaed;
}
.result-title { font-size: 14px; font-weight: 600; }
.result-body { flex: 1; overflow-y: auto; }
.result-content { padding: 16px 18px; }

.result-section { margin-bottom: 18px; }
.rs-title {
  font-size: 12px; font-weight: 600; color: #9ca3af;
  margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.04em;
}

.eq-box {
  background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 6px;
  padding: 10px 14px; font-family: 'Courier New', monospace; font-size: 13px;
  color: #0c4a6e; margin-bottom: 12px; word-break: break-all;
}

.metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.metric-box { background: #f0f2f5; border-radius: 6px; padding: 10px 12px; }
.mb-label { font-size: 11px; color: #9ca3af; margin-bottom: 2px; }
.mb-val { font-size: 18px; font-weight: 700; color: #1a1f2e; }

.interpretation-box {
  background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 6px;
  padding: 12px 14px; font-size: 12.5px; color: #0c4a6e; line-height: 1.7;
}
.interp-title { font-weight: 600; margin-bottom: 6px; }

.corr-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.corr-table th, .corr-table td { padding: 6px 8px; border: 1px solid #e8eaed; text-align: center; }
.corr-table th { background: #fafbfc; color: #9ca3af; font-weight: 500; }

.hyp-result { margin-bottom: 16px; }

.elbow-bar-wrap { position: relative; height: 18px; background: #f3f4f6; border-radius: 3px; overflow: hidden; }
.elbow-bar { height: 100%; border-radius: 3px; transition: width 0.3s; min-width: 2px; }
.elbow-bar-label { position: absolute; right: 6px; top: 1px; font-size: 10px; color: white; font-weight: 600; }

.empty-state { display: flex; justify-content: center; align-items: center; height: 400px; }
.header-actions { display: flex; align-items: center; gap: 10px; }

/* 混淆矩阵 */
.cm-grid { display: grid; gap: 2px; margin-top: 8px; }
.cm-cell { padding: 10px 14px; text-align: center; border-radius: 4px; font-size: 13px; font-weight: 500; background: #f3f4f6; }
.cm-header { background: #fafbfc; color: #6b7280; font-size: 12px; font-weight: 600; }
.cm-tp { background: #dcfce7; color: #166534; font-size: 18px; font-weight: 700; }
.cm-fp { background: #fef2f2; color: #991b1b; font-size: 18px; font-weight: 700; }
.stat-badge-row { margin-top: 10px; }
</style>
