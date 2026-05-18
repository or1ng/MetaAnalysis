# MetaAnalysis 元析智能

<p align="center">
  <b>国内首款集成统计学内核 + AI推理 + 自动化数据治理的智能数据分析平台</b>
</p>

<p align="center">
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

## ✨ 核心功能

### MVP 一期（当前进行中）
- 📁 **多源数据接入** — 支持 Excel/CSV 上传，自动识别编码和格式
- 🧹 **智能数据清洗** — 一键清洗 + 自定义规则，清洗过程全程留痕
- 💬 **AI 智能问答** — 支持复杂业务逻辑提问，不幻觉、不乱算
- 📊 **高阶统计分析** — 描述统计、假设检验、回归、聚类、时序分析
- 📈 **可视化图表** — ECharts 驱动，支持箱线图/热力图/QQ 图等统计图表
- 📝 **智能报告生成** — 商务汇报/学术论文/简约简报三种模板，一键导出

### 后续规划
- 🔍 **智能归因分析** — 自动判断因果/相关，量化各因素贡献度
- 📐 **指标口径统一引擎** — 解决企业跨表口径混乱的核心痛点
- 📄 **非结构化数据分析** — PDF/Word 表格提取、文本情感分析
- 🔒 **企业级合规** — 数据血缘、权限体系、操作审计日志

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 + Element Plus + ECharts + Vite | ≥3.4 |
| 后端 | FastAPI + SQLAlchemy + Alembic | ≥0.115 |
| 数据分析 | Pandas + Statsmodels + SciPy + Scikit-learn | ≥2.2 |
| 数据库 | MySQL | ≥8.0 |
| 报告导出 | python-docx + ReportLab + python-pptx | latest |
| AI 大模型 | OpenAI API / 兼容 OpenAI SDK 的国产大模型 | — |

---

## 📂 项目结构

```
MetaAnalysis/
├── metaanalysis_backend/          # 后端（FastAPI）
│   ├── api/                      # 接口路由层
│   ├── core/                     # 核心业务引擎（清洗/统计/AI/图表/导出）
│   ├── models/                   # SQLAlchemy 数据库模型
│   ├── schemas/                  # Pydantic 请求/响应模型
│   ├── services/                 # 业务逻辑层
│   ├── parser/                   # 文件解析器（Excel/CSV/PDF）
│   ├── main.py                   # FastAPI 入口
│   └── requirements.txt
│
├── metaanalysis_frontend/        # 前端（Vue 3）
│   ├── src/
│   │   ├── api/                 # 接口封装（request.js + 各模块 API）
│   │   ├── views/               # 页面组件
│   │   ├── router/              # 路由配置
│   │   └── store/               # Pinia 状态管理
│   └── package.json
│
├── prototypes/                   # 原型设计（8张 HTML 页面）
├── README.md
├── MetaAnalysis技术架构文档-MVP一期.md
├── MetaAnalysis产品多期规划.md
└── MetaAnalysis元析智能——产品完整功能架构清单（完整版）.md
```

---

## 🚀 快速启动

### 后端启动

```bash
cd metaanalysis_backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
# 启动后端（默认 8001 端口）
python main.py
```

### 前端启动

```bash
cd metaanalysis_frontend
npm install
# 启动前端开发服务器（默认 5173 端口）
npm run dev
```

### 访问

打开浏览器访问 `http://localhost:5173`

> ⚠️ 注意：前端 `.env.development` 中的 `VITE_API_BASE_URL` 需指向后端地址（默认 `http://localhost:8001`）

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [技术架构文档-MVP一期.md](./MetaAnalysis技术架构文档-MVP一期.md) | MVP 一期技术选型、目录结构、接口设计 |
| [产品多期规划.md](./MetaAnalysis产品多期规划.md) | 四期产品规划与功能全景对照表 |
| [产品完整功能架构清单（完整版）.md](./MetaAnalysis元析智能——产品完整功能架构清单（完整版）.md) | 四层产品架构与完整功能清单 |

---

## 🔄 产品多期规划

| 期数 | 状态 | 核心目标 |
|------|------|---------|
| MVP 一期 | 🔄 进行中 | 上传→清洗→分析→图表→报告 完整闭环 |
| MVP 二期 | 📋 待启动 | 报告导出Word/PDF、自定义章节、KPI告警 |
| MVP 三期 | 📋 规划中 | 归因分析、指标口径统一、非结构化分析 |
| MVP 四期 | 📋 规划中 | 数据血缘、权限审计、监控预警、多人协作 |

---

## 📝 开源协议

MIT License

---

> 如果这个项目对你有帮助，欢迎 ⭐ Star 支持！
