# 06 API 数据契约（始终生效）

> 全栈唯一契约。新增/修改端点必须同步：后端 `api/*.py` + CLAUDE.md §5 + 本文件。

## 统一响应格式

**成功响应**

```json
{ "code": 0, "message": "ok", "data": {} }
```

**分页响应**

```json
{ "code": 0, "message": "ok",
  "data": { "total": 100, "page": 1, "page_size": 20, "items": [] } }
```

**错误响应（业务错误码）**

```json
{ "code": 40001, "message": "人类可读的错误描述", "data": null }
```

## 规则

- 所有 API 返回上述格式，禁裸数据；**业务成功统一 `code === 0`**
- HTTP 状态码只表达传输层（2xx 成功、4xx 参数错、5xx 服务错）；业务失败统一 **HTTP 200 + code≠0**（全项目唯一约定，写死在 CLAUDE.md）
- 错误码为整数，分段预留：

| 段 | 含义 |
|---|---|
| 0 | 成功 |
| 40000~40099 | 参数/校验错误（40001 通用参数错误） |
| 40100~40199 | 认证与权限（40101 未登录） |
| 40300~40399 | DDL 拦截 / 操作被禁止（40301 SQL 含禁用语句） |
| 40400~40499 | 资源不存在 |
| 50000~50099 | 后端内部错误（50001 执行器异常） |
| 50100~50199 | 集群连接错误（50101 HS2 连接失败、50102 DS API 失败） |
| 50200~50299 | AI 服务错误（50201 模型超时） |

- 分页 `page` 从 1 开始、`page_size` 默认 20 最大 100；排序参数 `order_by`/`order` 可选
- 时间字段统一 ISO 8601：`2026-09-08T10:30:00+08:00`（见 14）
- 枚举/状态值统一小写字符串：`pending / running / success / failed`

## 端点清单（与 CLAUDE.md §5 对齐，四大能力）

**认证（预留）** `POST /api/v1/auth/login`
**健康检查** `GET /api/v1/health`

**数据源** `/api/v1/datasources`
- `POST` 创建（含类型 HIVE/MYSQL/POSTGRESQL、连接信息）；`GET` 列表
- `POST /{id}/test` 测试连接（3s 超时）；`POST /{id}/sync` 触发采集

**数据资产** `/api/v1/asset`
- `GET /databases?datasource_id=` 库列表
- `GET /tables?db_id=&keyword=&page=&page_size=` 表搜索（LIKE：表名+注释+字段名+字段注释）
- `GET /tables/{id}` 表详情（字段、分区、DDL）
- `GET /tables/{id}/usage` 使用统计（近 7 天热度）；`GET /tables/{id}/lineage` 血缘

**SQL 执行** `/api/v1/sql`
- `POST /execute` 请求 `{datasource_id, sql, limit?}` → 响应 `{execution_id}`
- `GET /status/{execution_id}` → `{status, rows, elapsed_ms}`
- `GET /result/{execution_id}` → 结果集（`items` 上限 10000 行，超限截断）
- `GET /result/{execution_id}/download` CSV 下载
- `POST /explain` 执行计划

**任务调度** `/api/v1/tasks` + `/api/v1/workflows`
- `POST /tasks`、`PUT /tasks/{id}`（自动存版本）、`POST /tasks/{id}/run`、`GET /tasks/{id}/executions`
- `POST /workflows/sync` 推送工作流到 DolphinScheduler；`GET /workflows/{id}/instances` 实例状态

**AI 智能** `/api/v1/ai`
- `POST /text-to-sql` 请求 `{question, datasource_id}` → `{sql, explain, confidence}`
- `POST /explain-sql`、`POST /optimize-sql`、`POST /dict`（智能数据字典）
