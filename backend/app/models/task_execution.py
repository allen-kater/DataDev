"""task_execution：执行记录（即席查询与任务执行共用，即 execution_id）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskExecution(Base):
    __tablename__ = "task_execution"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("task.id"), index=True)
    content: Mapped[Optional[str]] = mapped_column(Text)  # 那次跑的那段 SQL
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )  # pending / running / success / failed / canceled
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cost_ms: Mapped[Optional[int]] = mapped_column(Integer)
    result_rows: Mapped[Optional[int]] = mapped_column(Integer)
    result_path: Mapped[Optional[str]] = mapped_column(String(512))  # 大结果集落盘路径
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
