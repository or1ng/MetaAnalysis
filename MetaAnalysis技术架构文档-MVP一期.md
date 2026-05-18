# MetaAnalysis元析智能 — 技术架构文档（MVP一期）

> 版本：v1.0  
> 日期：2026-05-13  
> 阶段：原型固化期 → MVP一期研发期  
> 研发模式：个人轻量化开发

---

## 一、技术选型总览

| 层级 | 技术栈 | 版本建议 | 选型理由 |
|------|--------|---------|---------|
| **前端框架** | Vue 3 | ≥3.4 | Composition API，生态成熟 |
| **UI组件库** | Element Plus | ≥2.7 | B端后台首选，中文文档完善 |
| **图表库** | ECharts | ≥5.5 | 统计图表覆盖最全，支持箱线图/热力图/QQ图 |
| **HTTP客户端** | Axios | ≥1.7 | 请求拦截、Token管理 |
| **状态管理** | Pinia | ≥2.1 | 轻量，替代Vuex |
| **构建工具** | Vite | ≥5.4 | 开发热更新快 |
| **后端框架** | FastAPI | ≥0.115 | 异步高性能，自动生成Swagger文档 |
| **Python版本** | Python | ≥3.11 | 现代语法，性能提升 |
| **数据库** | MySQL | ≥8.0 | 成熟稳定，满足MVP需求 |
| **ORM** | SQLAlchemy | ≥2.0 | 异步支持，类型安全 |
| **数据库迁移** | Alembic | ≥1.13 | 与SQLAlchemy 2.0深度集成 |
| **数据分析** | Pandas | ≥2.2 | 数据处理核心 |
| **统计计算** | Statsmodels / SciPy | 最新版 | 覆盖全部高阶统计算法 |
| **Excel处理** | openpyxl | ≥3.1 | .xlsx读写 |
| **CSV处理** | 内置csv模块 | — | 轻量，无需额外依赖 |
| **PDF解析** | PyMuPDF (fitz) | ≥1.24 | 提取表格文本，速度快 |
| **Word生成** | python-docx | ≥1.1 | 生成.docx报告 |
| **PDF生成** | ReportLab | ≥4.2 | 生成.pdf报告 |
| **PPT生成** | python-pptx | ≥1.0 | 生成.pptx报告 |
| **AI大模型** | OpenAI API / 国产大模型API | — | 兼容OpenAI SDK格式即可 |
| **定时任务** | APScheduler | ≥3.10 | 监控预警巡检（二期） |
| **部署** | Docker + Nginx | 最新版 | 轻量化云服务器部署 |

---

## 二、项目目录结构

### 2.1 后端目录（Python FastAPI）

```
metaanalysis_backend/
├── main.py                        # FastAPI入口，挂载路由、CORS、生命周期
├── requirements.txt               # Python依赖清单
├── alembic.ini                    # Alembic数据库迁移配置
├── alembic/                       # 迁移脚本目录
│   └── versions/
│
├── api/                           # 接口路由层
│   ├── __init__.py
│   ├── auth.py                    # 登录/注册/Token刷新
│   ├── upload.py                  # 文件上传、数据集管理
│   ├── clean.py                   # 数据清洗（一键清洗、自定义规则）
│   ├── ai_chat.py                 # AI智能问答
│   ├── statistic.py               # 统计分析（描述/推断/回归/时序/聚类）
│   ├── chart.py                   # 图表生成与配置
│   ├── report.py                  # 报告生成与导出
│   └── user.py                    # 个人中心
│
├── core/                          # 核心业务引擎
│   ├── __init__.py
│   ├── clean_engine.py            # 数据清洗引擎（缺失值/异常值/重复值/格式校准）
│   ├── stat_engine.py             # 统计算法引擎（Statsmodels/SciPy封装）
│   ├── ai_engine.py               # AI推理引擎（Prompt编排/上下文记忆/逻辑拆解）
│   ├── chart_engine.py            # 图表渲染引擎（ECharts配置生成）
│   ├── export_engine.py           # 报告导出引擎（Word/PDF/PPT生成）
│   └── parser/                    # 文件解析器
│       ├── __init__.py
│       ├── excel_parser.py        # Excel解析（.xlsx/.xls）
│       ├── csv_parser.py          # CSV解析（自动检测编码）
│       └── pdf_parser.py          # PDF表格提取
│
├── models/                        # SQLAlchemy数据库模型
│   ├── __init__.py
│   ├── user.py                    # 用户表
│   ├── dataset.py                 # 数据集表
│   ├── task.py                    # 分析任务表
│   ├── report.py                  # 报告表
│   └── clean_log.py               # 清洗日志表
│
├── schemas/                       # Pydantic请求/响应模型
│   ├── __init__.py
│   ├── auth.py
│   ├── dataset.py
│   ├── clean.py
│   ├── ai_chat.py
│   ├── statistic.py
│   ├── chart.py
│   └── report.py
│
├── services/                      # 业务逻辑层（调用core引擎）
│   ├── __init__.py
│   ├── auth_service.py
│   ├── dataset_service.py
│   ├── clean_service.py
│   ├── ai_service.py
│   ├── stat_service.py
│   ├── chart_service.py
│   └── report_service.py
│
├── config/                        # 配置管理
│   ├── __init__.py
│   └── settings.py                # 环境变量、数据库URL、AI API Key等
│
├── utils/                         # 通用工具
│   ├── __init__.py
│   ├── file_utils.py              # 文件存储路径管理
│   ├── security.py                # JWT Token生成/验证
│   └── response.py                # 统一响应格式封装
│
└── uploads/                       # 用户上传文件存储目录（按用户ID分目录）
```

### 2.2 前端目录（Vue3 + Vite）

```
metaanalysis_frontend/
├── index.html
├── vite.config.js
├── package.json
├── .env.development               # 开发环境API地址
├── .env.production                # 生产环境API地址
│
├── public/
│   └── favicon.ico
│
└── src/
    ├── main.js                    # Vue应用入口
    ├── App.vue                    # 根组件
    ├── router/
    │   └── index.js               # 路由配置（含导航守卫）
    ├── store/
    │   └── index.js               # Pinia全局状态
    │
    ├── layout/                    # 全局布局组件
    │   ├── MainLayout.vue         # 左侧导航 + 顶栏 + 内容区 + 底栏
    │   ├── Sidebar.vue            # 左侧导航菜单
    │   ├── Header.vue             # 顶部面包屑/用户信息/消息
    │   └── Footer.vue             # 底部状态栏
    │
    ├── views/                     # 页面视图（对应8张原型）
    │   ├── login/
    │   │   └── Login.vue          # 登录/注册页
    │   ├── home/
    │   │   └── Dashboard.vue      # 工作台首页
    │   ├── data/
    │   │   └── DataManage.vue     # 数据上传与管理
    │   ├── clean/
    │   │   └── DataClean.vue      # 智能数据清洗
    │   ├── aiChat/
    │   │   └── AiChat.vue         # AI智能问答
    │   ├── statistic/
    │   │   └── Statistics.vue     # 高阶统计分析
    │   ├── chart/
    │   │   └── ChartStudio.vue    # 智能可视化图表
    │   ├── report/
    │   │   └── ReportGen.vue      # 自动化报告生成
    │   └── user/
    │       └── UserCenter.vue     # 个人中心
    │
    ├── components/                # 公共可复用组件
    │   ├── DataTable.vue          # 数据表格（排序/筛选/分页）
    │   ├── StatCard.vue           # 统计卡片
    │   ├── ChartPanel.vue         # ECharts图表封装
    │   ├── FileUpload.vue         # 文件上传组件（拖拽区）
    │   ├── ChatBubble.vue         # AI对话气泡
    │   └── ReportPreview.vue      # 报告预览组件
    │
    ├── api/                       # 后端API请求封装
    │   ├── request.js             # Axios实例（拦截器/Token/错误处理）
    │   ├── auth.js
    │   ├── dataset.js
    │   ├── clean.js
    │   ├── aiChat.js
    │   ├── statistic.js
    │   ├── chart.js
    │   └── report.js
    │
    └── assets/                    # 静态资源
        ├── styles/
        │   ├── variables.css      # CSS变量（主题色/字号/间距）
        │   └── global.css         # 全局样式重置
        └── images/
```

---

## 三、数据库设计（MySQL 8.0）

### 3.1 ER关系图概览

```
users 1──N datasets
users 1──N tasks
users 1──N reports
datasets 1──N clean_logs
datasets 1──N tasks
tasks  1──1 reports
```

### 3.2 表结构明细

#### users — 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 用户ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希（bcrypt） |
| role | ENUM('free','pro','admin') | DEFAULT 'free' | 角色权限 |
| avatar_url | VARCHAR(500) | | 头像URL |
| storage_used | BIGINT | DEFAULT 0 | 已用存储（字节） |
| storage_limit | BIGINT | DEFAULT 536870912 | 存储上限（默认512MB） |
| status | ENUM('active','disabled') | DEFAULT 'active' | 账号状态 |
| created_at | DATETIME | DEFAULT NOW() | 注册时间 |
| updated_at | DATETIME | ON UPDATE NOW() | 更新时间 |

#### datasets — 数据集表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 数据集ID |
| user_id | BIGINT | FK → users.id, NOT NULL | 所属用户 |
| name | VARCHAR(200) | NOT NULL | 数据集名称 |
| file_type | ENUM('xlsx','csv','pdf','txt') | NOT NULL | 原始文件类型 |
| file_path | VARCHAR(500) | NOT NULL | 服务器存储路径 |
| file_size | BIGINT | DEFAULT 0 | 文件大小（字节） |
| row_count | INT | DEFAULT 0 | 数据行数 |
| col_count | INT | DEFAULT 0 | 数据列数 |
| columns_json | JSON | | 字段元数据（名称/类型/缺失率） |
| is_cleaned | TINYINT(1) | DEFAULT 0 | 是否已清洗 |
| cleaned_path | VARCHAR(500) | | 清洗后文件路径 |
| version | INT | DEFAULT 1 | 当前版本号 |
| status | ENUM('processing','ready','error') | DEFAULT 'processing' | 处理状态 |
| created_at | DATETIME | DEFAULT NOW() | 上传时间 |
| updated_at | DATETIME | ON UPDATE NOW() | 更新时间 |

#### clean_logs — 清洗日志表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 日志ID |
| dataset_id | BIGINT | FK → datasets.id, NOT NULL | 关联数据集 |
| action_type | VARCHAR(50) | NOT NULL | 操作类型（fill_missing/remove_outlier/deduplicate/normalize/format） |
| params_json | JSON | | 操作参数 |
| affected_rows | INT | DEFAULT 0 | 影响行数 |
| result_summary | TEXT | | 处理结果摘要 |
| snapshot_path | VARCHAR(500) | | 操作前快照路径（用于回溯） |
| created_at | DATETIME | DEFAULT NOW() | 操作时间 |

#### tasks — 分析任务表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 任务ID |
| user_id | BIGINT | FK → users.id, NOT NULL | 所属用户 |
| dataset_id | BIGINT | FK → datasets.id, NOT NULL | 使用的数据集 |
| task_type | ENUM('ai_chat','statistic','chart','clean','auto_explore') | NOT NULL | 任务类型 |
| config_json | JSON | | 任务配置参数 |
| status | ENUM('pending','running','completed','failed') | DEFAULT 'pending' | 任务状态 |
| result_json | JSON | | 分析结果 |
| error_msg | TEXT | | 失败原因 |
| duration_sec | FLOAT | | 执行耗时（秒） |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| completed_at | DATETIME | | 完成时间 |

#### reports — 报告表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 报告ID |
| user_id | BIGINT | FK → users.id, NOT NULL | 所属用户 |
| task_id | BIGINT | FK → tasks.id | 关联分析任务 |
| title | VARCHAR(200) | NOT NULL | 报告标题 |
| template | ENUM('business','academic','simple') | DEFAULT 'business' | 报告模板 |
| format | ENUM('docx','pdf','pptx') | NOT NULL | 导出格式 |
| content_json | JSON | | 报告内容结构（章节/图表/结论） |
| file_path | VARCHAR(500) | | 生成的报告文件路径 |
| file_size | BIGINT | DEFAULT 0 | 文件大小 |
| status | ENUM('generating','ready','failed') | DEFAULT 'generating' | 生成状态 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

---

## 四、API接口清单

### 4.1 认证模块 `/api/auth`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/auth/register` | 用户注册 | `{username, email, password}` | `{user_id, token}` |
| POST | `/api/auth/login` | 用户登录 | `{username, password}` | `{token, refresh_token}` |
| POST | `/api/auth/refresh` | Token刷新 | `{refresh_token}` | `{token}` |
| GET | `/api/auth/me` | 获取当前用户信息 | — | `{user}` |

### 4.2 数据管理模块 `/api/datasets`

| 方法 | 路径 | 说明 | 请求体/参数 | 响应 |
|------|------|------|------------|------|
| POST | `/api/datasets/upload` | 上传文件 | `FormData(file)` | `{dataset}` |
| GET | `/api/datasets/` | 数据集列表 | `?page=1&size=20` | `{total, items}` |
| GET | `/api/datasets/{id}` | 数据集详情 | — | `{dataset}` |
| GET | `/api/datasets/{id}/preview` | 数据预览 | `?page=1&size=50` | `{columns, rows, total}` |
| PUT | `/api/datasets/{id}` | 重命名/更新 | `{name}` | `{dataset}` |
| DELETE | `/api/datasets/{id}` | 删除数据集 | — | `{message}` |
| POST | `/api/datasets/{id}/backup` | 创建备份 | — | `{backup_path}` |
| GET | `/api/datasets/{id}/columns` | 字段元数据 | — | `{columns: [{name, type, missing_rate}]}` |

### 4.3 数据清洗模块 `/api/clean`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/clean/auto/{dataset_id}` | 一键智能清洗 | — | `{clean_log, preview}` |
| POST | `/api/clean/custom/{dataset_id}` | 自定义清洗 | `{actions: [{type, params}]}` | `{clean_log, preview}` |
| GET | `/api/clean/logs/{dataset_id}` | 清洗日志列表 | `?page=1&size=20` | `{total, items}` |
| POST | `/api/clean/rollback/{log_id}` | 回溯到指定操作 | — | `{dataset}` |
| POST | `/api/clean/restore/{dataset_id}` | 还原到原始数据 | — | `{dataset}` |
| GET | `/api/clean/summary/{dataset_id}` | 清洗报告 | — | `{dirty_ratio, actions_taken, suggestions}` |

### 4.4 AI智能问答模块 `/api/ai`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/ai/chat` | 发送问答 | `{dataset_id, message, conversation_id?}` | `{reply, charts?, reasoning?}` |
| GET | `/api/ai/conversations` | 对话记录列表 | `?page=1&size=20` | `{total, items}` |
| GET | `/api/ai/conversations/{id}` | 对话详情 | — | `{messages}` |
| DELETE | `/api/ai/conversations/{id}` | 删除对话 | — | `{message}` |
| POST | `/api/ai/auto-explore/{dataset_id}` | 全自动数据探索 | — | `{insights, charts, summary}` |

### 4.5 统计分析模块 `/api/statistic`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/statistic/descriptive` | 描述统计 | `{dataset_id, columns[], group_by?}` | `{summary_table, distribution}` |
| POST | `/api/statistic/hypothesis` | 假设检验 | `{dataset_id, test_type, columns[], params}` | `{test_result, p_value, conclusion}` |
| POST | `/api/statistic/correlation` | 相关性分析 | `{dataset_id, columns[], method?}` | `{matrix, p_values, heatmap_config}` |
| POST | `/api/statistic/regression` | 回归分析 | `{dataset_id, dependent, independents[], model_type}` | `{coefficients, r_squared, predictions}` |
| POST | `/api/statistic/timeseries` | 时序分析 | `{dataset_id, time_col, value_col, params}` | `{decomposition, trend, forecast}` |
| POST | `/api/statistic/clustering` | 聚类分析 | `{dataset_id, columns[], n_clusters, method}` | `{labels, centers, silhouette_score}` |

### 4.6 可视化图表模块 `/api/chart`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/chart/generate` | 生成图表配置 | `{dataset_id, chart_type, x, y, params}` | `{echarts_option}` |
| GET | `/api/chart/templates` | 图表模板列表 | — | `{templates}` |
| POST | `/api/chart/batch` | 批量自动出图 | `{dataset_id, chart_types[]}` | `{charts: [{type, option}]}` |
| POST | `/api/chart/save` | 保存图表 | `{dataset_id, name, config}` | `{chart_id}` |
| GET | `/api/chart/saved/{dataset_id}` | 已保存图表列表 | — | `{charts}` |

### 4.7 报告生成模块 `/api/report`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/report/generate` | 生成报告 | `{dataset_id, template, format, include_charts, include_statistics, include_suggestions}` | `{report_id, status}` |
| GET | `/api/report/{id}` | 报告详情 | — | `{report}` |
| GET | `/api/report/{id}/preview` | 报告预览 | — | `{content_html}` |
| GET | `/api/report/{id}/download` | 下载报告 | — | `File (docx/pdf/pptx)` |
| GET | `/api/report/` | 报告列表 | `?page=1&size=20` | `{total, items}` |
| DELETE | `/api/report/{id}` | 删除报告 | — | `{message}` |

### 4.8 用户中心模块 `/api/user`

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/user/profile` | 获取个人信息 | — | `{user}` |
| PUT | `/api/user/profile` | 更新个人信息 | `{username?, email?, avatar?}` | `{user}` |
| PUT | `/api/user/password` | 修改密码 | `{old_password, new_password}` | `{message}` |
| GET | `/api/user/storage` | 存储用量 | — | `{used, limit, usage_percent}` |

---

## 五、统一响应格式

所有API接口遵循统一响应结构：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

错误响应：
```json
{
  "code": 400,
  "message": "参数校验失败：columns不能为空",
  "data": null
}
```

状态码规范：

| code | 含义 |
|------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token过期/无效） |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 数据处理校验失败 |
| 500 | 服务器内部错误 |

---

## 六、开发环境搭建

### 6.1 环境要求

| 工具 | 版本 |
|------|------|
| Python | ≥ 3.11 |
| Node.js | ≥ 18 |
| MySQL | ≥ 8.0 |
| Git | 最新版 |
| VS Code | 最新版（推荐） |

### 6.2 后端环境搭建

```bash
# 1. 创建项目目录
mkdir metaanalysis && cd metaanalysis
mkdir metaanalysis_backend metaanalysis_frontend

# 2. 进入后端目录，创建虚拟环境
cd metaanalysis_backend
python -m venv venv

# Windows激活
venv\Scripts\activate

# 3. 安装依赖
pip install fastapi uvicorn sqlalchemy alembic pandas numpy
pip install statsmodels scipy scikit-learn
pip install openpyxl pymupdf python-docx reportlab python-pptx
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
pip install pydantic-settings httpx
pip install openai  # 或其他兼容OpenAI SDK的大模型库

# 4. 导出依赖清单
pip freeze > requirements.txt

# 5. 初始化Alembic数据库迁移
alembic init alembic

# 6. 配置数据库连接（编辑config/settings.py）
# DATABASE_URL = "mysql+aiomysql://root:password@localhost:3306/metaanalysis"

# 7. 创建数据库
mysql -u root -p -e "CREATE DATABASE metaanalysis DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 8. 生成数据库表
alembic revision --autogenerate -m "initial tables"
alembic upgrade head

# 9. 启动后端服务
uvicorn main:app --reload --port 8000

# 10. 访问Swagger文档
# http://localhost:8000/docs
```

### 6.3 前端环境搭建

```bash
# 1. 进入前端目录
cd metaanalysis_frontend

# 2. 使用Vite创建Vue3项目
npm create vite@latest . -- --template vue

# 3. 安装核心依赖
npm install element-plus @element-plus/icons-vue
npm install vue-router@4 pinia
npm install axios
npm install echarts vue-echarts
npm install @vueup/vue-quill  # 富文本编辑器（报告编辑用）

# 4. 安装开发依赖
npm install -D unplugin-auto-import unplugin-vue-components

# 5. 配置自动导入（vite.config.js）
# Element Plus 按需导入，减少打包体积

# 6. 启动开发服务器
npm run dev

# 开发服务器默认地址：http://localhost:5173
```

### 6.4 环境变量配置

后端 `.env` 文件：

```ini
# 应用配置
APP_NAME=MetaAnalysis元析智能
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production

# 数据库
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/metaanalysis

# JWT配置
JWT_SECRET=your-jwt-secret-key
JWT_EXPIRE_MINUTES=1440
JWT_REFRESH_EXPIRE_DAYS=7

# AI大模型配置
AI_API_KEY=your-ai-api-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o

# 文件存储
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=52428800

# 跨域配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

前端 `.env.development`：

```ini
VITE_API_BASE_URL=http://localhost:8000/api
```

前端 `.env.production`：

```ini
VITE_API_BASE_URL=https://your-domain.com/api
```

---

## 七、核心引擎设计概要

### 7.1 数据清洗引擎（clean_engine.py）

```
输入：DataFrame + 清洗配置
  │
  ├─ 缺失值检测 → 填充策略（均值/中位数/众数/插值/自定义值）
  ├─ 异常值检测 → IQR法 / Z-Score法 / 孤立森林 → 标记/截断/替换
  ├─ 重复值检测 → 精确匹配 / 模糊匹配 → 去重保留首条
  ├─ 格式校准 → 数据类型转换 / 单位统一 / 大小写标准化
  └─ 清洗报告生成 → 脏数据占比 / 处理明细 / 优化建议
      │
输出：清洗后DataFrame + 清洗日志
```

### 7.2 统计算法引擎（stat_engine.py）

```
输入：DataFrame + 分析参数
  │
  ├─ 描述统计 → count/mean/std/min/max/median/Q1/Q3/IQR/skew/kurtosis
  ├─ 假设检验 → t检验 / 卡方检验 / ANOVA / Mann-Whitney U / KS检验
  ├─ 相关分析 → Pearson / Spearman / Kendall + 偏相关
  ├─ 回归分析 → OLS多元线性回归 + 模型评价(R²/Adj-R²/F统计量/DW)
  ├─ 时序分析 → STL分解 / ADF检验 / ARIMA预测
  └─ 聚类挖掘 → K-Means / DBSCAN / 层次聚类 + 轮廓系数
      │
输出：统计结果 + 显著性标注 + ECharts配置 + 文本结论
```

### 7.3 AI推理引擎（ai_engine.py）

```
用户输入：自然语言问题 + 当前数据集上下文
  │
  ├─ 意图识别 → 分析类型判定（统计/可视化/归因/对比/预测）
  ├─ 逻辑拆解 → 复杂问题分解为子任务序列
  ├─ 代码生成 → 根据子任务生成Pandas/Statsmodels代码
  ├─ 安全执行 → 沙箱执行生成的代码
  ├─ 结果解读 → 将数值结果转为业务语言
  └─ 图表联动 → 自动生成配套可视化配置
      │
输出：文本回答 + 图表 + 推理过程展示
```

### 7.4 报告导出引擎（export_engine.py）

```
输入：分析结果 + 报告模板 + 导出格式
  │
  ├─ 内容组装 → 封面 + 摘要 + 数据概况 + 图表 + 结论 + 建议
  ├─ Word导出 → python-docx模板填充
  ├─ PDF导出 → ReportLab排版渲染
  └─ PPT导出 → python-pptx幻灯片生成
      │
输出：文件流（docx/pdf/pptx）
```

---

## 八、MVP一期开发执行顺序

按照产品文档规定的顺序，分8个步骤推进：

| 步骤 | 任务 | 前端页面 | 后端模块 | 预计工时 |
|------|------|---------|---------|---------|
| 1 | 基础框架搭建 | MainLayout + Login | auth + main.py入口 | 2天 |
| 2 | 数据上传与管理 | DataManage | upload + parser（Excel/CSV/PDF） | 3天 |
| 3 | 智能数据清洗 | DataClean | clean_engine + clean API | 3天 |
| 4 | 统计算法引擎 | Statistics | stat_engine + statistic API | 4天 |
| 5 | 可视化图表 | ChartStudio | chart_engine + chart API | 3天 |
| 6 | AI智能问答 | AiChat | ai_engine + ai_chat API | 4天 |
| 7 | 报告生成导出 | ReportGen | export_engine + report API | 4天 |
| 8 | 个人中心 + 联调 | UserCenter + 全局 | user API + 联调Bug修复 | 3天 |

**MVP一期总预计工时：约26个工作日（~5周）**

---

## 九、一期不开发功能清单（二期迭代）

以下功能明确推迟到二期，一期禁止触碰：

- 指标口径统一引擎
- 归因分析模块
- 非结构化数据解析（文本情感/关键词/图像识别）
- 自定义可视化大屏（拖拽搭建）
- 智能业务决策建议
- 监控预警模块
- 数据库直连接入（MySQL/Oracle/达梦）
- 数据血缘追溯
- 权限管理 / 数据脱敏 / 水印
- 审计日志
- 私有化部署

---

## 十、关键技术约束

1. **零代码原则**：所有分析功能通过UI操作完成，用户无需编写代码
2. **可溯源原则**：所有计算结果必须附带算法参数、显著性和溯源信息
3. **留痕原则**：清洗操作全程记录日志，支持回溯还原
4. **安全原则**：AI生成的代码在沙箱环境中执行，禁止直接操作文件系统
5. **轻量化原则**：一期单机部署，无需分布式架构
