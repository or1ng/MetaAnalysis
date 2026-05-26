# MetaAnalysis 元析智能

<p align="center">
  <b>集成统计学内核 + AI推理 + 自动化数据治理的智能数据分析平台</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/版本-v2.0-brightgreen.svg" />
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" />
  <img src="https://img.shields.io/badge/Vue-3.4+-green.svg" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-orange.svg" />
  <img src="https://img.shields.io/badge/MySQL-8.0+-blue.svg" />
</p>

---

## 🎯 产品定位

MetaAnalysis 元析智能，补齐市面所有 BI、AI 分析工具的通病，打造**自带统计学内核 + 深度 AI 推理 + 全自动数据治理 + 业务决策闭环**的新一代智能分析平台。

| 对比维度 | 传统BI | 通用AI | **MetaAnalysis** |
|---------|--------|--------|----------------|
| 统计模型 | ❌ 高阶统计阉割 | ❌ 不严谨、乱算 | ✅ 内置完整统计内核 |
| 数据质量 | ❌ 口径混乱无解 | ❌ 不识别数据问题 | ✅ 自动清洗+口径对齐 |
| 归因分析 | ❌ 无 | ❌ 幻觉严重 | ✅ 量化贡献度、区分因果/相关 |
| 合规审计 | ✅ 有 | ❌ 无 | ✅ 血缘+日志+权限全覆盖 |

---

## ✨ 功能概览

### MVP 一期（v2.0 当前版本）

| 模块 | 状态 | 说明 |
|------|:----:|------|
| 📁 多源数据接入 | ✅ 完成 | Excel/CSV 上传，自动识别编码和格式 |
| 🧹 智能数据清洗 | ✅ 完成 | 一键清洗 + 自定义规则，清洗过程全程留痕 |
| 💬 AI 智能问答 | ✅ 完成 | 支持复杂业务逻辑提问，不幻觉、不乱算 |
| 📊 基础统计分析 | ✅ 完成 | 描述统计、假设检验（T检验/卡方/方差分析）、相关分析、线性回归 |
| 🔬 P1 高阶统计引擎 | ✅ 完成 | 逻辑回归（ROC/AUC）、PCA降维、DBSCAN聚类、ARIMA时序预测 |
| 📈 可视化图表 | ✅ 完成 | 柱状图、折线图、**面积图**、饼图、散点图、箱线图、直方图；批量出图；**PNG导出** |
| 📝 智能报告生成 | ✅ 完成 | 商务汇报/学术论文/简约简报三种模板，HTML 预览 |

### v2.0 新增亮点

- 🔬 **P1 Engine**：逻辑回归 / PCA / DBSCAN / ARIMA，内置自动参数选择（BIC定阶、eps自适应）
- 📈 **面积图**：可视化新增面积图类型，平滑渐变填充
- 🖼️ **PNG 导出**：图表 2x 高清导出
- 🗂️ **多图同屏**：批量生成后以 2 列网格展示所有图表，点击卡片切换主视图
- 🔌 **Vite Proxy**：前端统一 `/api/` 前缀，告别硬编码 baseURL

### 后续规划

- 🔍 **智能归因分析** — 自动判断因果/相关，量化各因素贡献度
- 📐 **指标口径统一引擎** — 解决企业跨表口径混乱的核心痛点
- 📄 **报告多格式导出** — Word / PDF / PPT
- 🔒 **企业级合规** — 数据血缘、权限体系、操作审计日志

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 + Element Plus + ECharts + Vite | ≥3.4 |
| 后端 | FastAPI + SQLAlchemy | ≥0.115 |
| 数据分析 | Pandas + Statsmodels + SciPy + Scikit-learn | ≥2.2 |
| 数据库 | MySQL | ≥8.0 |
| AI 大模型 | OpenAI API / 兼容 OpenAI SDK 的国产大模型 | — |

---

## 📂 项目结构

```
MetaAnalysis/
├── metaanalysis_backend/          # 后端（FastAPI）
│   ├── api/                      # 接口路由层
│   │   ├── chart.py              # 可视化接口（7种图表 + 字段识别）
│   │   ├── statistic.py          # 统计接口（基础 + P1 Engine）
│   │   ├── ai_chat.py            # AI 问答接口
│   │   ├── clean.py              # 智能清洗接口
│   │   ├── report.py             # 报告生成接口
│   │   └── upload.py             # 数据上传接口
│   ├── services/
│   │   ├── statistic_service.py  # 统计引擎（含 P1Engine）
│   │   └── clean_service.py      # 清洗引擎
│   ├── parser/                   # 文件解析器（Excel/CSV，含日期启发式检测）
│   ├── models/                   # SQLAlchemy 数据库模型
│   ├── schemas/                  # Pydantic 请求/响应模型
│   ├── main.py                   # FastAPI 入口
│   └── requirements.txt
│
├── metaanalysis_frontend/        # 前端（Vue 3）
│   ├── src/
│   │   ├── api/                 # 接口封装（request.js + 各模块 API）
│   │   ├── views/               # 页面组件
│   │   │   ├── chart/ChartStudio.vue    # 可视化图表工作台
│   │   │   ├── statistic/Statistics.vue # 统计分析（含 P1 面板）
│   │   │   ├── AiChat.vue               # AI 问答
│   │   │   ├── DataClean.vue            # 智能清洗
│   │   │   ├── ReportGen.vue            # 报告生成
│   │   │   └── Dashboard.vue            # 数据看板
│   │   ├── router/              # 路由配置
│   │   └── store/               # Pinia 状态管理
│   ├── .env.development         # 开发环境变量
│   └── package.json
│
├── prototypes/                   # 原型设计（8张 HTML 页面）
├── VERSION-v2.0变更日志.md       # 本次版本详细变更记录
├── MetaAnalysis技术架构文档-MVP一期.md
├── MetaAnalysis产品多期规划.md
└── MetaAnalysis元析智能——产品完整功能架构清单（完整版）.md
```

---

## 🚀 快速启动

### 后端启动

```bash
cd metaanalysis_backend

# 创建并激活虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# 如需运行测试，安装开发依赖
pip install -r requirements-dev.txt

# 复制本地环境变量模板
copy .env.example .env
# macOS/Linux:
# cp .env.example .env

# 启动后端（8001 端口）
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### 前端启动

```bash
cd metaanalysis_frontend
npm install

# 启动前端开发服务器（5173 端口，自动代理 /api → localhost:8001）
npm run dev
```

### 访问

打开浏览器访问 `http://localhost:5173`

> 前端通过 Vite Proxy 将 `/api/*` 请求转发到后端 8001 端口，无需手动配置跨域。

---

## 工程化补充

### 环境配置

- 后端环境变量模板：`metaanalysis_backend/.env.example`
- 前端环境变量模板：`metaanalysis_frontend/.env.example`
- 开发环境默认使用 SQLite：`sqlite+aiosqlite:///./metaanalysis.db`
- 生产环境请更换 `SECRET_KEY`，并按实际部署环境配置 `DATABASE_URL`、`AI_API_KEY` 和 `CORS_ORIGINS`

### 启动自检

后端启动后可检查：

```bash
curl http://localhost:8001/health
curl http://localhost:8001/
```

`/health` 应返回 `{"status":"ok"}`，根接口返回的 `version` 应与 `APP_VERSION` 一致。

### 本地验证

后端：

```bash
cd metaanalysis_backend
pytest -q
```

前端：

```bash
cd metaanalysis_frontend
npm run build
```

### CI

仓库已补充 GitHub Actions：

- `.github/workflows/backend-ci.yml`：安装后端依赖并运行 pytest
- `.github/workflows/frontend-ci.yml`：安装前端依赖并运行 Vite build

---

## 🔌 API 速览

### 统计分析 `/api/statistic/`

| 端点 | 说明 |
|------|------|
| `GET /fields/{dataset_id}` | 获取字段分类（数值/文本/日期） |
| `POST /describe` | 描述统计 |
| `POST /correlation` | 相关分析 |
| `POST /regression` | 线性回归 |
| `POST /logistic` | **逻辑回归（P1）** — ROC/AUC/混淆矩阵 |
| `POST /pca` | **PCA 降维（P1）** — 特征值/方差解释/载荷矩阵 |
| `POST /dbscan` | **DBSCAN 聚类（P1）** — 密度聚类/散点图数据 |
| `POST /arima` | **ARIMA 预测（P1）** — 自动定阶/预测/置信区间 |

### 可视化 `/api/chart/`

| 端点 | 说明 |
|------|------|
| `GET /templates` | 获取图表类型列表 |
| `GET /fields/{dataset_id}` | 获取字段分类 |
| `POST /generate` | 生成图表（支持 bar/line/area/pie/scatter/boxplot/histogram） |
| `POST /batch` | 批量自动出图 |

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [开发与验证指南](./docs/DEVELOPMENT.md) | 本地环境配置、启动自检、数据库说明和验证命令 |
| [项目补齐清单](./docs/PROJECT_COMPLETION.md) | 当前工程化补齐内容与下一步建议 |
| [VERSION-v2.0变更日志.md](./VERSION-v2.0变更日志.md) | v2.0 详细变更记录（文件级 diff） |
| [技术架构文档-MVP一期.md](./MetaAnalysis技术架构文档-MVP一期.md) | MVP 一期技术选型、目录结构、接口设计 |
| [产品多期规划.md](./MetaAnalysis产品多期规划.md) | 四期产品规划与功能全景对照表 |
| [产品完整功能架构清单（完整版）.md](./MetaAnalysis元析智能——产品完整功能架构清单（完整版）.md) | 四层产品架构与完整功能清单 |

---

## 🔄 版本历史

| 版本 | 日期 | 核心内容 |
|------|------|---------|
| **v2.0** | 2026-05-22 | P1 Engine（逻辑回归/PCA/DBSCAN/ARIMA）+ 可视化升级（面积图/PNG导出/多图网格）+ Vite Proxy |
| v1.0 | 2026-05 | MVP 一期基础版：上传/清洗/基础统计/图表/报告 完整闭环 |

---

## 🗺️ 产品多期规划

| 期数 | 状态 | 核心目标 | 预估工期 |
|------|:----:|---------|:-------:|
| MVP 一期 | 🔄 进行中 | 上传→清洗→分析→图表→报告 完整闭环 | ~26 工作日 |
| MVP 二期 | 📋 待启动 | 报告导出 Word/PDF/PPT、自定义章节、KPI 告警 | ~20 工作日 |
| MVP 三期 | 📋 规划中 | 归因分析、指标口径统一、非结构化分析 | ~30 工作日 |
| MVP 四期 | 📋 规划中 | 数据血缘、权限审计、监控预警、多人协作 | ~40 工作日 |

---

## 📝 开源协议

MIT License

---

## 👤 作者

**Sonick**
- 硕士：埃克塞特大学 数据科学与统计学
- 公众号：`趋势哨`

---

> 如果这个项目对你有帮助，欢迎 ⭐ Star 支持！
