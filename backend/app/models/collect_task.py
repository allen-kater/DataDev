"""collect_task：元数据采集任务（APScheduler 调度）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CollectTask(Base):
    __tablename__ = "collect_task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    datasource_id: Mapped[int] = mapped_column(
        ForeignKey("datasource.id"), nullable=False
    )
    schedule: Mapped[Optional[str]] = mapped_column(String(64))  # cron 表达式
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
