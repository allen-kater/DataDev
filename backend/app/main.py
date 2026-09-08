"""FastAPI 入口：路由注册、静态资源托管（生产模式）、CORS（开发模式）。

启动：`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`（scripts/start.ps1 封装）。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import ai, asset, auth, health, schedule, sql
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import get_logger
from app.core.scheduler import start_scheduler

settings = get_settings()
logger = get_logger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("初始化数据库表结构（幂等）...")
    await init_db()
    # 采集器挂载到后端进程（APScheduler，rules/04：不单起进程）
    start_scheduler()
    logger.info("后端启动完成")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

for r in (
    health.router,
    asset.router,
    asset.datasource_router,
    sql.router,
    schedule.router,
    schedule.workflow_router,
    ai.router,
    auth.router,
):
    app.include_router(r, prefix=API_PREFIX)

# 生产模式：frontend 构建产物输出到 backend/app/static 后由 FastAPI 托管
_static_dir = Path(settings.static_dir)
if _static_dir.is_dir() and any(_static_dir.iterdir()):
    # /assets 静态资源 + SPA 兜底（非 API 路径一律回退 index.html，支持前端 history 路由）
    if (_static_dir / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        index = _static_dir / "index.html"
        if not index.exists():
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "前端未构建"}, status_code=404)
        return FileResponse(index)

    logger.info("已托管前端静态资源: %s", _static_dir)
