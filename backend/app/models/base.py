"""SQLAlchemy 声明基类与公共 Mixin。"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类。"""


class TimestampMixin:
    """公共字段：created_at（UTC 存储，+08:00 输出见 rules/14）。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
