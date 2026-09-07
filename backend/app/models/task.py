"""task：任务定义（对齐 4.1.4 五态状态机）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Task(Base, TimestampMixin):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)  # 项目分组（B22，预留）
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    task_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="SQL"
    )  # SQL / SHELL / PYTHON / SPARK / FLINK / DATAX
    content: Mapped[Optional[str]] = mapped_column(Text)
    datasource_id: Mapped[Optional[int]] = mapped_column(ForeignKey("datasource.id"))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT"
    )  # DRAFT → TRIAL_SUCCESS → SCHEDULED → PAUSED → OFFLINE
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"))
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
