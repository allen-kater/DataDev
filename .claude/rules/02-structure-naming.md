# 02 目录 / 命名（始终生效）

> 适用：所有代码。结构以 `docs/架构设计方案.md` 第 6.2 节为唯一基准。

## 目录结构（禁止自行发明新顶层目录）

```
backend/
  app/
    main.py            # 唯一入口（含静态资源托管开关）
    api/               # 路由层：asset.py / sql.py / schedule.py / ai.py / auth.py
    services/          # 业务逻辑：collector.py / sql_executor.py / ds_client.py / ai_service.py / lineage.py
    models/            # SQLAlchemy：每实体一文件（user.py / datasource.py / table_meta.py ...）
    schemas/           # Pydantic：每路由一文件（与 models 分离，不复用）
    core/              # config.py / logging.py / database.py / security.py / ddl_guard.py
  config.yaml          # 集群连接配置（密码字段走环境变量注入，不入库）
  requirements.txt
frontend/
  src/
    views/             # 页面级组件（按能力：asset / sql / schedule / ai / system）
    components/        # 公共组件
    stores/            # Pinia（user / datasource / query ...）
    api/               # 后端接口封装（axios，统一错误处理）
    utils/             # 工具
    constants/         # UI 文案集中地（禁硬编码中文）
    assets/styles/     # 全局样式 / 主题变量（见 03）
  vite.config.ts       # dev 代理 → http://127.0.0.1:8000
scripts/               # start.ps1 / stop.ps1 / common.ps1
data/                  # dataflow.db / results / uploads / run(PID) —— 全部 gitignore
logs/                  # backend.log / frontend.log / ollama.log —— 全部 gitignore
docs/                  # 架构设计方案.md（权威）/ 环境探测结果.md / ADR/
.claude/rules/         # 本目录，编号 00~14
```

## 命名规范

| 对象 | 规则 | 示例 |
|---|---|---|
| Python 模块/包 | snake_case | `sql_executor.py` |
| Python 类 | PascalCase | `SqlExecutor`, `DatasourceService` |
| SQLAlchemy 模型 | 单数 snake_case，类名 PascalCase 复数域避免 | `TableMeta` → 表 `table_meta` |
| API 路由前缀 | 复数名词 | `/api/v1/datasources` |
| 前端组件文件 | PascalCase 匹配组件名 | `TableDetail.vue` |
| Pinia store | useXxxStore | `useDatasourceStore` |
| 常量 | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE` |
| 表字段 | snake_case | `last_sync_at` |

## 分层依赖规则

- `api/` → `services/` → `models/` / `core/`；**禁路由层直接写 SQL、禁 service 层直接操作请求对象**
- Pydantic Schema 与 SQLAlchemy Model 分离，不复用
- 新增 API 端点：必须同文件落到对应 `api/*.py`，并同步 CLAUDE.md 第 5 节 + rules/06

## 其它

- 单文件 ≤ 400 行、单函数 ≤ 50 行（超限即拆，见 CLAUDE.md §6）
- 新文件必须"确有必要"才创建，优先改现有文件
