"""table_meta：表元数据（HMS TBLS + SDS + TABLE_PARAMS 落地）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TableMeta(Base):
    __tablename__ = "table_meta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    database_id: Mapped[int] = mapped_column(
        ForeignKey("database_meta.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_type: Mapped[Optional[str]] = mapped_column(String(32))  # MANAGED / EXTERNAL / VIRTUAL_VIEW
    location: Mapped[Optional[str]] = mapped_column(String(1024))  # 仅展示字符串，不做文件操作
    input_format: Mapped[Optional[str]] = mapped_column(String(255))
    output_format: Mapped[Optional[str]] = mapped_column(String(255))
    serde: Mapped[Optional[str]] = mapped_column(String(255))
    num_rows: Mapped[Optional[int]] = mapped_column(BigInteger)
    num_files: Mapped[Optional[int]] = mapped_column(BigInteger)
    total_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_ddl_time: Mapped[Optional[int]] = mapped_column(BigInteger)  # Hive 秒级时间戳
    create_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_access_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    view_text: Mapped[Optional[str]] = mapped_column(Text)  # 视图原始 SQL（血缘来源）
    owner: Mapped[Optional[str]] = mapped_column(String(128))
    comment: Mapped[Optional[str]] = mapped_column(String(512))
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 软删
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
