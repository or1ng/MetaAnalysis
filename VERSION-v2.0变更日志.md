# MetaAnalysis元析智能 — v2.0 变更日志

> 基准版本：GitHub 发布版 (D:\MetaAnalysis-upload)  
> 当前版本：2026-05-22 开发版

---

## 一、版本总览

| 维度 | v1.0 (发布版) | v2.0 (当前) | 增量 |
|------|:---:|:---:|:---:|
| 后端源文件 | 33 .py | 33 .py | — |
| 前端源文件 | 35 | 36 | +1 |
| 原型文件 | 9 .html | 9 .html | — |
| 新增可运行页面 | — | DataManage.vue（数据中心） | +1 |

---

## 二、新增文件 (2)

| 文件 | 说明 |
|------|------|
| `metaanalysis_frontend/.env.development` | 环境变量：`VITE_API_BASE_URL=http://localhost:8001` |
| `metaanalysis_frontend/src/views/data/DataManage.vue` | **数据中心页面**（368行）：数据集列表+上传管理+基本信息展示 |

---

## 三、后端变更 (4 文件，+32KB)

### 3.1 `services/statistic_service.py`（31KB → 55KB，+23KB）
**P1 Engine — 4个增强算法模块**

| 模块 | 方法 | 核心能力 |
|------|------|----------|
| 逻辑回归 | `logistic_regression()` | 二分类+标准化+混淆矩阵+ROC/AUC+特征系数 |
| PCA 降维 | `pca()` | 特征值+方差解释+载荷矩阵+碎石图数据 |
| DBSCAN 聚类 | `dbscan()` | 密度聚类+自动eps/min_samples+散点图数据 |
| ARIMA 时序 | `arima()` | 自动定阶(BIC)+残差检验+预测+置信区间 |

### 3.2 `api/statistic.py`（9KB → 14KB，+5KB）
- 新增 4 个 P1 路由：`/api/statistic/logistic\|pca\|dbscan\|arima`
- `_classify_columns()` 重构：中文关键词（年/月/日/日期/时间/年份/月份）+ `\b` 单词边界 + 启发式日期值采样 + `datetime64[ns, UTC]` 支持 + 纯整数ID排除 + 数值型日期列检测
- 新增 `/column-values/{dataset_id}` 端点（分组检验用）

### 3.3 `api/chart.py`（15KB → 18KB，+3KB）
- `_classify_columns()` 从 statistic.py 同步完整版
- 新增面积图类型（`area`）：复用折线图逻辑 + `areaStyle.opacity=0.3`

### 3.4 `parser/file_parser.py`（8KB → 9KB，+1KB）
- `extract_metadata` 新增启发式日期字符串检测（采样20条正则匹配≥80%命中率即标记 datetime）
- 整数列也加入日期关键词匹配（如 year/month 整数列）

---

## 四、前端变更 (6 文件)

### 4.1 `Statistics.vue`（36KB → 66KB，+30KB）— **最大变更**
**P1 算法前端面板**：
- 逻辑回归：因变量选择（binaryCandidateFields 过滤）+ 自变量多选 + ROC曲线/AUC/混淆矩阵
- PCA：主成分数滑块 + 累计方差图 + 载荷矩阵表 + 碎石图
- DBSCAN：eps/min_samples 参数 + 散点图着色 + 簇统计
- ARIMA：时序字段选择（仅 dateFields）+ 预测期数 + 预测图 + 残差检验

**字段过滤增强**：
- 时序分析/ARIMA 时间列 → 仅日期字段（dateFields）
- 逻辑回归 Y 列 → binaryCandidateFields（文本+数值，排除日期）
- computed `binaryCandidateFields`

### 4.2 `ChartStudio.vue`（10KB → 12KB，+2KB）
- 面积图 radio-button
- PNG 导出按钮（ECharts `getDataURL()` 2x pixelRatio）
- 批量图表网格视图（2列栅格，独立 ECharts 实例管理）
- 清理逻辑：`destroyBatchGrid()` 在 unmount/数据集切换/单图生成时调用

### 4.3 `statistic.js`（0.7KB → 1.2KB）
- 新增 4 个 P1 接口函数：`logistic()` / `pca()` / `dbscan()` / `arima()`
- 新增 `getColumnValues()`

### 4.4 `vite.config.js`（273B → 425B）
```diff
+ server: {
+   port: 5173,
+   proxy: { '/api': { target: 'http://localhost:8001', changeOrigin: true } }
+ }
```

### 4.5 `request.js`
```diff
- baseURL: 'http://localhost:8001'
+ baseURL: ''
```
改用 vite proxy 代理，消除硬编码。

### 4.6 `main.js`
- 移除 `import './style.css'`（精简非必要样式引入）

---

## 五、未变更文件

| 分类 | 文件数 | 清单 |
|------|:---:|------|
| 后端（30个） | 30 | main.py, requirements.txt, api/ai_chat.py, api/auth.py, api/clean.py, api/report.py, api/upload.py, api/user.py, config/, core/, models/ (5), schemas/ (2), services/clean_service.py, services/dataset_service.py, utils/ (3), 所有 `__init__.py` |
| 前端（22个） | 22 | index.html, package.json, .gitignore, HelloWorld.vue, MainLayout.vue, router/, store/, api/aiChat.js, api/auth.js, api/chart.js, api/clean.js, api/dataset.js, api/report.js, AiChat.vue, DataClean.vue, Dashboard.vue, Login.vue, ReportGen.vue, UserCenter.vue, App.vue, style.css, global.css, variables.css |
| 原型（9个） | 9 | 全部 .html（page1-page8 + index） |
| 产品文档（4个） | 4 | 产品多期规划、技术架构文档、功能架构清单、README |

---

## 六、关键架构决策

1. **Vite Proxy 取代硬编码 baseURL** — 前端所有 API 路径统一 `/api/` 前缀，vite dev server 代理到 localhost:8001
2. **`_classify_columns` 三处统一** — statistic.py / chart.py / report.py 使用相同字段分类逻辑
3. **P1 Engine 独立类** — `P1Engine` 在 statistic_service.py 中与 `StatisticEngine` 并列，不污染原有接口
4. **编码原则更新** — Andrej Karpathy CLAUDE.md 四原则（先想再写/简单优先/手术级改动/目标驱动）

---

## 七、已知待办

| 优先级 | 条目 | 所属模块 |
|:---:|------|------|
| P2 | 热力图（chart.py 缺 heatmap option 生成函数） | 可视化 |
| P2 | 数据标签开关 | 可视化 |
| P2 | 报告导出 Word/PDF/PPT（当前仅HTML） | 报告 |
| — | 全链路回归测试 | 联调 |

---

*生成时间：2026-05-22 15:20*
