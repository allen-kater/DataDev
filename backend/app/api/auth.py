"""认证路由（预留）：POST /api/v1/auth/login。"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
