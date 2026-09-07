# 04 后端规则（写 backend/** 时生效）

## 分层与代码结构

- `api/` 只做参数校验与响应包装；业务在 `services/`；数据访问只经 SQLAlchemy `models/`
- Pydantic Schema 与 Model 分离：`schemas/` 管请求/响应形状，`models/` 管表结构
- 配置统一走 `core/config.py` + `config.yaml`（密码/密钥字段由环境变量注入，禁硬编码）
- 所有环境相关配置走配置层，不在业务代码里直接读环境变量

## 数据库（SQLAlchemy async）

- 一律 async session：`async with SessionLocal() as session`，禁同步阻塞调用
- 表结构与 `docs/架构设计方案.md` 第 7 章一致；新表先补方案（走 ADR）再编码
- 时间字段统一 datetime（UTC 存、+08:00 出，见 14）；软删除字段 `is_deleted`
- SQLite 无方言兼容问题：使用标准 SQLAlchemy 类型，禁写 MySQL 专有 SQL（除非切库时经 ADR）

## SQL 执行器（核心模块）

- 提交即返回 `execution_id`；状态机 `PENDING → RUNNING → SUCCESS/FAILED`（不可跳步），客户端轮询
- 执行超时上限 30 分钟，超时自动 kill；结果集最多 10000 行，超出截断并提示
- 大结果集落盘 `data/results/`，小结果入库；支持 CSV 下载（后端生成文件返回链接）
- 执行记录必须写 `sql_execution` / `query_log`（谁、何时、什么 SQL、耗时）
- 每条执行后解析 SQL 提取涉及表名，写入 `table_usage`（血缘/热度数据来源）

## DDL 拦截（安全第一道）

- 执行前用 sqlglot 解析 SQL，禁执行：`CREATE/DROP/ALTER TABLE`、`TRUNCATE`、`DROP DATABASE`
- 默认仅允许 SELECT（课设安全叙事对齐）；开放 DML 必须单独角色 + 审批流（走 ADR）
- 拦截逻辑收敛在 `core/ddl_guard.py`，任何 SQL 入口（含 AI 生成的 SQL）都必须过它

## 元数据采集器

- 增量采集：对比 `table_name + 字段 hash`，只更新变化部分（按 `transient_lastDdlTime` / `last_sync_at` 过滤）
- 采集失败不影响已有数据：新数据写临时，成功后替换；单次超时 5 分钟，超时中断并记错误
- 完成后更新 `datasource.last_sync_at`
- 采集器是 APScheduler 后台任务，**不单起进程**（内存红线）

## 调度对接（DolphinScheduler 客户端）

- 只封装 DS OpenAPI：token 生成 → 项目/工作流定义 CRUD → 触发/查询实例
- 平台存任务定义，推送 DS 时映射为工作流 JSON；Cron/DAG/重试/告警全部委托 DS
- DS 版本差异（2.x/3.x）以探测结果为准，客户端内部做版本适配层
- 平台侧不实现第二套调度引擎（铁律）

## AI 服务

- 统一走 OpenAI 兼容接口调 Ollama（`/v1/chat/completions`），模型路由配置化（Phase 6 可切云端）
- Text2SQL 的 RAG 上下文来自平台元数据库（LIKE 检索 + prompt 拼接，MVP 不建向量库）
- AI 生成的 SQL 必须过 DDL 拦截 + EXPLAIN 校验；任何写操作/发布调度必须人审
- AI 交互记录写 `ai_query`（问题、上下文、SQL、是否采纳）

## 通用

- 单文件 ≤ 400 行、单函数 ≤ 50 行
- 日志统一 `core/logging.py`（分模块 logger），禁 print；日志禁输出密码/token
- 异步阻塞调用（pyhive 同步库）放 `ThreadPoolExecutor`，不阻塞 event loop
