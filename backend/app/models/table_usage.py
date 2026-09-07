"""table_usage：表使用记录（热度数据来源）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TableUsage(Base):
    __tablename__ = "table_usage"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(
        ForeignKey("table_meta.id"), index=True, nullable=False
    )
    execution_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("task_execution.id")
    )
    used_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sys_user.id"))
