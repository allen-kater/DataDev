"""任务调度路由（Phase 4 实现，骨架阶段仅注册空路由）。

端点契约见 rules/06：
- /api/v1/tasks      任务定义 CRUD / run / executions
- /api/v1/workflows  工作流同步 / 实例状态
"""

from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["task"])
workflow_router = APIRouter(prefix="/workflows", tags=["workflow"])
