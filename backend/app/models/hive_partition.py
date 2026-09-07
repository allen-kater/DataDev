"""hive_partition：Hive 分区（大表分页关键）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class HivePartition(Base, TimestampMixin):
    __tablename__ = "hive_partition"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(
        ForeignKey("table_meta.id"), index=True, nullable=False
    )
    partition_spec: Mapped[str] = mapped_column(String(512), nullable=False)  # 如 dt=2026-09-07
    location: Mapped[Optional[str]] = mapped_column(String(1024))
    num_rows: Mapped[Optional[int]] = mapped_column(BigInteger)
    total_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
