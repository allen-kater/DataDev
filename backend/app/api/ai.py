"""AI 智能路由（Phase 5 实现，骨架阶段仅注册空路由）。

端点契约见 rules/06：
- POST /api/v1/ai/text-to-sql
- POST /api/v1/ai/explain-sql
- POST /api/v1/ai/optimize-sql
- POST /api/v1/ai/dict
"""

from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["ai"])
