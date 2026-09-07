# 09 测试（写测试/提交前生效）

## 策略（个人单机、轻量）

- 后端：pytest + pytest-asyncio；前端：Vitest（纯逻辑）+ Playwright（E2E 验证，截图留证）
- 优先级：核心链路必须测 —— SQL 执行状态机、DDL 拦截、元数据增量采集、DS 客户端映射、统一响应格式
- 测试隔离：SQLite 用内存库或临时文件库（`data/test.db`），不污染 `data/dataflow.db`

## 后端规范

- 目录 `backend/tests/`，镜像 `app/` 结构：`tests/api/test_sql.py`、`tests/services/test_ddl_guard.py`
- 命名：`test_<功能>_<场景>`，如 `test_execute_rejects_ddl`
- DDL 拦截必须有参数化用例：`CREATE/DROP/ALTER/TRUNCATE/DROP DATABASE` 全覆盖
- 与集群相关的用例标记 `@pytest.mark.integration`，本地默认跳过（无集群时 CI/本地不跑），用 `pytest -m integration` 显式跑
- 统一响应格式断言：`code === 0` / 分页 / 错误码分段

## 前端规范

- 纯逻辑（sql 解析、结果分页、状态映射）放 `frontend/src/utils/` 并配 Vitest
- E2E：Playwright 覆盖关键路径（登录预留 → 数据源列表 → 执行 SQL → 看结果），截图存 `docs/e2e/`（gitignore）

## 提交门槛

- 改动含核心逻辑时必须补/跑对应测试
- `pytest` 全绿才进入 verify 阶段；测试失败不回退代码，先修复到绿
- 测试不写"表面测试"（只断言 200）：至少断言业务 `code` 与关键字段
