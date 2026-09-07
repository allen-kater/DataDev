"""collect_log：采集执行日志。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CollectLog(Base):
    __tablename__ = "collect_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("collect_task.id"), nullable=False)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cost_sec: Mapped[Optional[int]] = mapped_column(Integer)
    tables_scanned: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
