"""健康检查：GET /api/v1/health。

返回 {status, version, db, cluster_reach}，方便 start.ps1 与排障使用。
集群连通性检查 Phase 3 接入真实探测，骨架阶段返回 null。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.schemas.common import ApiResponse, ok

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse)
async def health(
    session: AsyncSession = Depends(get_session),
) -> ApiResponse:
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    settings = get_settings()
    data = {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": settings.app_version,
        "db": db_status,
        "cluster_reach": {"hs2": None, "hms": None, "ds": None},
    }
    return ok(data)
