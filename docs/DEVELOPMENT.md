# 开发与验证指南

这份文档补齐项目的工程化入口：如何配置环境、如何确认服务跑通、以及每次改动的最小验证标准。

## 基本原则

- 先跑通，再扩展功能。
- 每次只改一个目标，避免顺手重构无关代码。
- 新增功能必须配一个可执行的验证方式：命令、测试、接口检查或手动验收路径。
- 如果 README、接口返回值和配置项出现版本或端口不一致，以配置文件为准并同步修正文档。

## 后端环境

```bash
cd metaanalysis_backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

macOS/Linux 激活虚拟环境时使用：

```bash
source venv/bin/activate
```

启动后检查：

```bash
curl http://localhost:8001/health
curl http://localhost:8001/
```

预期：`/health` 返回 `{"status":"ok"}`，根接口返回的 `version` 应与 `APP_VERSION` 一致。

## 数据库说明

默认开发环境使用 SQLite：

```env
DATABASE_URL=sqlite+aiosqlite:///./metaanalysis.db
```

应用启动时会调用 `init_db()` 初始化数据库。生产环境如果切换 MySQL，需要先明确异步驱动方案并补充依赖，例如 `asyncmy` 或 `aiomysql`，再更新 `DATABASE_URL` 和迁移说明。

## 前端环境

```bash
cd metaanalysis_frontend
npm install
npm run dev
```

开发服务默认运行在 `http://localhost:5173`。Vite 会把 `/api/*` 代理到 `http://localhost:8001`。

## 本地验证

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

## 当前优先待补

1. 全链路回归测试：上传数据、清洗、统计、图表、报告预览。
2. 报告导出：Word、PDF、PPT。
3. 图表增强：热力图和数据标签开关。
4. 生产部署说明：MySQL、密钥、CORS、文件存储、反向代理。
