# 10 安全（始终生效，违反即停）

## 集群与网络

- 平台到集群**只走单端口协议**（REST / JDBC / Thrift：HS2 10000、HMS MySQL 3306、DS API 12345）
- **禁 HDFS NameNode/DataNode RPC 直连**（8020/9864）——Windows 无法解析集群 hostname 会卡死
- 集群地址一律存 IP，禁存/用 hostname（铁律 1）
- 只读原则：采集只允许 SELECT；数据源账号只授 SELECT（DDL 拦截第二道防线）

## 凭据

- 密码/token 入库前 AES 加密（`core/security.py`），读取时解密，禁明文落库/落日志/落响应
- 连接配置在 `config.yaml`，密码字段用环境变量注入（`${VAR}` 占位），`config.yaml` 不入库
- 日志（含 AI 上下文、SQL 记录）禁输出密码/token/密钥
- 连接测试 3 秒超时，禁无超时连接阻塞

## DDL 与写操作

- 所有 SQL 入口（含 AI 生成）过 `core/ddl_guard.py`：拦截 `CREATE/DROP/ALTER/TRUNCATE/DROP DATABASE`
- 默认仅 SELECT；开放 DML 需单独角色 + 审批流（走 ADR）
- 任何写操作（建生产表、发布调度到 DS）必须**人审**后才执行（AI 只生成建议，不自动执行）

## 审计

- 所有 SQL 执行写 `query_log`（谁、何时、SQL、耗时、来源：手写/AI）
- AI 问答写 `ai_query`（问题、注入上下文、生成 SQL、是否采纳）
- 任务/工作流变更存版本（`task_version`），可回溯

## 依赖与配置

- 引入新依赖必须满足 rules/01 技术栈锁版；禁引入重型组件（ES/Atlas/DataHub）
- 禁在代码中硬编码密钥；`.env` / `*.key` 不入库（见 .gitignore）
- 前端 axios 统一拦截器处理错误，禁在响应中透出后端堆栈/连接串
