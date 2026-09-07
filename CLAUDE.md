# DataDev 数据开发平台

> 本文件是本项目 AI 助手的**入口文件**（Claude Code / Cursor 启动时自动加载）。
> 详细设计唯一权威来源：`docs/架构设计方案.md`。所有规则见 `.claude/rules/`（编号 00~14）。
> 本文件只做 5 分钟索引，详细约束进 Rules，不在这里堆细节。

## 1. 项目简介

轻量级一站式数据开发平台，四大能力：

1. **数据资产管理**：元数据自动采集（HMS 直读 + HS2 兜底）、数据地图、表/字段检索、血缘、资产概览
2. **SQL 在线开发**：Monaco 编辑器、多数据源、执行历史、结果预览、EXPLAIN 查看
3. **任务调度**：复用 VM 集群的 DolphinScheduler（OpenAPI 对接），平台只做薄封装
4. **AI 智能层**：Text2SQL、SQL 优化、慢 SQL 诊断、智能数据字典（Ollama 本地模型）

运行形态：**Windows 宿主机原生进程**（无 Docker / K8s），计算全部下发到 VMware 内 3 节点 Hive 集群（hadoop102/103/104）。

## 2. 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| 后端 | Python 3.11/3.12 + FastAPI + SQLAlchemy 2.0(async) + Pydantic v2 | uvicorn 单 worker |
| 前端 | Vue3 + Vite + TypeScript(strict) + Element Plus + Monaco Editor + Pinia + Vue Router + ECharts | 单 SPA Shell |
| 元数据库 | SQLite（MVP，`data/dataflow.db`）| SQLAlchemy 可无缝切本地 MySQL/MariaDB |
| 计算引擎 | HiveServer2（Thrift 10000，**IP 直连**）| pyhive；Spark STS 为可选增强 |
| 调度 | DolphinScheduler OpenAPI（REST）| 复用集群已有，**禁自研第二调度引擎** |
| AI | Ollama 本地模型（qwen2.5-coder:7b 等）+ OpenAI 兼容 API | 独立进程，不在 2GB 预算内 |
| 部署 | 原生进程 + `scripts/start.ps1` / `stop.ps1` | 禁 Docker |
| 辅助库 | httpx、sqlglot（DDL 拦截/血缘/校验）、APScheduler（采集）、apscheduler | AI 层用 langchain/openai sdk |

## 3. 项目结构

```
D:\AI\DataDev\
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口（含静态资源托管开关）
│   │   ├── api/               # 路由：asset / sql / schedule / ai / auth
│   │   ├── services/          # 资产采集 / SQL 执行器 / DS 客户端 / AI 服务
│   │   ├── models/            # SQLAlchemy 模型（每实体一个文件）
│   │   └── core/              # 配置、日志、DB 会话、DDL 拦截
│   ├── config.yaml            # 集群 IP/端口/账号（加密字段走环境变量）
│   ├── requirements.txt
│   └── .venv/
├── frontend/
│   ├── src/                   # components / views / stores / api / utils / constants
│   └── vite.config.ts         # dev 代理→8000；build 输出到 backend/app/static
├── scripts/                   # start.ps1 / stop.ps1 / common.ps1
├── data/                      # dataflow.db / results / uploads / run(PID)
├── logs/
├── docs/                      # 架构设计方案.md（唯一权威）、环境探测结果.md
└── .claude/rules/             # 编号规则 00~14
```

## 4. API 规范

- 所有 API 前缀：`/api/v1/`
- 响应体统一：`{ "code": 0, "message": "ok", "data": {...} }`（0 成功、非 0 失败）
- 分页参数：`page`（从 1 开始）、`page_size`（默认 20，最大 100），响应 `{total, page, page_size, items}`
- 时间格式：ISO 8601，时区 `Asia/Shanghai`（`+08:00`），如 `2026-09-08T10:30:00+08:00`
- 错误：HTTP 状态码表示传输层问题；业务失败统一 `HTTP 200 + code≠0`，`message` 人类可读
- 业务错误码：整数，见 `.claude/rules/06-api-contract.md`

## 5. 核心 API 端点

```
健康检查：  GET    /api/v1/health
数据源：    POST   /api/v1/datasources                  创建数据源
            GET    /api/v1/datasources                  列表
            POST   /api/v1/datasources/{id}/test        测试连接
            POST   /api/v1/datasources/{id}/sync        触发元数据同步
数据资产：  GET    /api/v1/databases                    库列表（按数据源筛选）
            GET    /api/v1/tables                       表列表（搜索/筛选）
            GET    /api/v1/tables/{id}                  表详情（字段/分区/DDL）
            GET    /api/v1/tables/{id}/usage            使用统计
            GET    /api/v1/tables/{id}/lineage          血缘
SQL 执行：  POST   /api/v1/sql/execute                  提交 SQL（返回 execution_id）
            GET    /api/v1/sql/status/{id}              查询状态
            GET    /api/v1/sql/result/{id}              获取结果
            POST   /api/v1/sql/explain                  执行计划
任务调度：  POST   /api/v1/tasks                        创建任务
            PUT    /api/v1/tasks/{id}                   更新（自动存版本）
            POST   /api/v1/tasks/{id}/run               手动执行
            GET    /api/v1/tasks/{id}/executions        执行历史
            POST   /api/v1/workflows/sync               推送工作流到 DolphinScheduler
AI 智能：   POST   /api/v1/ai/text-to-sql               自然语言转 SQL
            POST   /api/v1/ai/explain-sql               SQL 解释
            POST   /api/v1/ai/optimize-sql              SQL 优化建议
            POST   /api/v1/ai/dict                      智能数据字典生成
认证(预留)： POST   /api/v1/auth/login
```

## 6. 开发约定

- 单文件不超过 400 行，超过必须拆分
- 单函数不超过 50 行
- 所有数据库操作走 SQLAlchemy async session，禁同步 ORM
- 新增 API 必须同步更新本文件第 5 节端点列表 + `rules/06` 契约
- 前端所有 UI 文本放 `frontend/src/constants/`，不硬编码中文字符串
- 涉及集群的地址一律存 IP（禁 hostname，见铁律 1），密码加密存储（AES）
- 平台自身不做计算：所有 SQL/作业下发集群执行（铁律 2）

## 7. 开发流程（ECC + 多 Agent）

强制阶段顺序，任一阶段失败则停止，不跳步：

```
plan → tdd → implement → code-review → testing → verify
```

| 阶段 | 职责 | 典型 Agent |
|---|---|---|
| plan | 对齐 `docs/架构设计方案.md` 契约、拆任务、识别风险 | planner |
| tdd | RED → GREEN → 重构 | tdd-guide |
| implement | 改 backend/frontend，遵守 Rules | 主会话 / impl |
| code-review | 规范与安全、API 形状、DDL 拦截 | code-reviewer |
| testing | pytest、关键路径 | tester |
| verify | Playwright 截图留证 | verifier |

个人单机环境：无依赖子任务可并行多 Agent；每功能收尾清理。详细说明见 `rules/12`。

## 8. 安全与禁止项（红线，违反即停）

- NEVER `git push`，除非用户明确要求
- NEVER 无确认删库、改集群任何组件配置、覆盖集群已有数据
- NEVER 让本地客户端直连 HDFS NameNode/DataNode RPC（8020/9864）
- NEVER 引入 Docker、Elasticsearch、Atlas/DataHub 等重型组件（2GB 内存红线）
- NEVER 在日志、SQL、响应中输出密钥/密码明文
- NEVER 平台侧执行计算（Hive 引擎计算必须在集群）
- NEVER code-review 未通过就进入 testing

## 9. 当前开发阶段

仓库骨架阶段。里程碑见 `docs/架构设计方案.md` 第 9 章（Phase 0~6，勿与参考文档 4.2.3 的"Phase 1~7"编号混用）：

- Phase 0 环境探测：待执行（`docs/环境探测结果.md` 为结果模板）
- Phase 1 平台骨架：待启动
- 详细计划随进展更新到 `docs/`，不散落在对话里
