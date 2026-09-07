# 01 技术栈锁版（违反即拒绝）

> 适用：所有代码。引入任何新依赖前先读本文件，不满足即拒绝或走 ADR。

## 后端

- Python 3.11 / 3.12，FastAPI，SQLAlchemy 2.0 **async 模式**，Pydantic v2
- 数据库操作必须 async session，**禁同步 ORM**（sync_engine 仅用于初始化建表）
- 元数据库：SQLite（`data/dataflow.db`，MVP）；SQLAlchemy 连接串可切本地 MySQL/MariaDB，**禁直接复用 VM 上 MySQL 与 HMS 账本同实例**
- HTTP 客户端：httpx（async），**不用 requests**
- Hive 对接：pyhive（Thrift 直连 HS2）；若与集群 Hive 版本不兼容 → 备选 JayDeBeApi 桥接官方 Hive JDBC 驱动（需走 ADR 并标注）
- SQL 解析/校验/血缘：sqlglot（DDL 拦截第一道、静态校验、血缘提取统一复用它）
- 调度采集：APScheduler（采集器作为后端进程内任务，**不单起进程**）
- AI：openai sdk（Ollama 提供 OpenAI 兼容端点）；可选 langchain-core
- 严禁引入：Flask / Django / 同步 ORM / Elasticsearch 客户端 / 重型平台 SDK

## 前端

- Vue3（Composition API）+ Vite + TypeScript（**strict，禁 any**）+ Element Plus + Pinia + Vue Router
- 编辑器：Monaco Editor（`@guolao/vue-monaco-editor` 或官方 wrapper）
- 图表：ECharts
- 样式：scoped CSS + Element Plus 主题变量 + 全局 CSS 变量（见 03），**禁引入 Tailwind/其他 CSS 框架**
- Node 18+ / 20 LTS；包管理统一 npm

## 进程与部署

- 禁 Docker；统一 `scripts/start.ps1`（prod/dev 两模式）、`scripts/stop.ps1`、`scripts/common.ps1`
- 端口：后端 8000、Vite dev 5173、Ollama 11434、MCP 8080（可选）。冲突时 `DATAFLOW_PORT` 环境变量改端口
- Ollama 独立进程，不计入 2GB 平台预算

## 数据模型

- 表名/字段与 `docs/架构设计方案.md` 第 7 章一一对应，新增表需先在方案中补充再编码（走 ADR）
- 命名：表名 snake_case 单数（`table_meta`、`column_meta`）；主键统一 `id` int 自增；时间字段统一 `*_at` datetime

## 版本约束清单（待环境探测确认）

| 组件 | 版本 | 状态 |
|---|---|---|
| Hive / HiveServer2 | ? | 待探测，决定 pyhive 兼容与 HS2 端口 |
| Spark Thrift Server | ? | 待探测，可选增强前置 |
| DolphinScheduler | 2.x / 3.x | 待探测，决定 API 路径与认证方式 |
| HMS MySQL | ? | 待探测，决定采集 SQL 方言 |
