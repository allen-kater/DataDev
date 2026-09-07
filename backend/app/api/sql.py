"""SQL 在线开发路由（Phase 3 实现，骨架阶段仅注册空路由）。

端点契约见 rules/06：
- POST /api/v1/sql/execute   提交 SQL（返回 execution_id）
- GET  /api/v1/sql/status/{id}
- GET  /api/v1/sql/result/{id}  及 /download
- POST /api/v1/sql/explain
"""

from fastapi import APIRouter

router = APIRouter(prefix="/sql", tags=["sql"])
