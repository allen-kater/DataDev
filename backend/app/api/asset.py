"""数据资产管理路由（Phase 2 实现，骨架阶段仅注册空路由）。

端点契约见 rules/06 与 CLAUDE.md 第 5 节：
- /api/v1/datasources  数据源 CRUD / test / sync
- /api/v1/asset        库 / 表 / 详情 / usage / lineage
"""

from fastapi import APIRouter

router = APIRouter(prefix="/asset", tags=["asset"])
datasource_router = APIRouter(prefix="/datasources", tags=["datasource"])
