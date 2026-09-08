"""APScheduler 定时采集调度（rules/04：采集器为后端进程内任务，不单起进程）。

设计：
- AsyncIOScheduler 与 FastAPI 事件循环同进程；
- 固定间隔扫描 enabled 的采集任务（collect_task），触发 run_collect；
- 内存红线：单进程后台任务，无额外进程。
"""

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.collect_task import CollectTask

logger = get_logger(__name__)

# 采集周期（秒）：MVP 固定 30 分钟，collect_task.schedule(cron) 留待后续扩展
COLLECT_INTERVAL_SEC = 30 * 60


async def _run_scheduled_collects() -> None:
    """扫描 enabled 采集任务并逐个执行（失败不影响其它）。"""
    from sqlalchemy import select

    async with SessionLocal() as session:
        tasks = (
            await session.execute(select(CollectTask).where(CollectTask.enabled.is_(True)))
        ).scalars().all()
        for task in tasks:
            try:
                await _collect_one(task.datasource_id)
            except Exception as exc:  # noqa: BLE001 - 单任务失败不中断扫描
                logger.error("定时采集失败 task=%s ds=%s: %s", task.id, task.datasource_id, exc)


async def _collect_one(datasource_id: int) -> None:
    from app.services.collector import run_collect

    async with SessionLocal() as session:
        await run_collect(session, datasource_id)


def start_scheduler() -> AsyncIOScheduler:
    """启动调度器（幂等）：应用 lifespan 中调用。"""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _run_scheduled_collects,
        trigger=IntervalTrigger(seconds=COLLECT_INTERVAL_SEC),
        id="scheduled_metadata_collect",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("定时采集调度已启动（间隔 %ss）", COLLECT_INTERVAL_SEC)
    return scheduler
