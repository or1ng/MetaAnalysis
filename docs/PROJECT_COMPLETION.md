# 项目补齐清单

基于当前 v2.0 状态，项目下一步不应优先堆叠新功能，而应先补齐可运行、可验证、可维护的基础内容。

## 已补齐

- 后端 `.env.example`，明确版本、数据库、JWT、AI、上传和 CORS 配置。
- 后端开发依赖 `requirements-dev.txt`，用于安装测试工具。
- 后端最小 pytest，验证 `/health`、根接口版本和 OpenAPI 版本来源。
- 前后端 GitHub Actions，分别执行后端测试和前端构建。
- 根目录 `.gitignore`，避免提交本地数据库、上传文件、虚拟环境和构建产物。
- 独立 `LICENSE` 文件，与 README 中的 MIT 声明一致。
- `docs/DEVELOPMENT.md`，补充启动、自检、数据库和验证说明。

## 下一步建议

1. 把变更日志中的待办转成 GitHub issues。
2. 为上传、清洗、统计、图表和报告生成补端到端回归测试。
3. 实现热力图和数据标签开关。
4. 实现 Word/PDF/PPT 报告导出。
5. 补生产部署文档，包括 MySQL 驱动、迁移、密钥和反向代理。
