"""database_meta：库元数据（HMS DBS 表落地）。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DatabaseMeta(Base):
    __tablename__ = "database_meta"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    datasource_id: Mapped[int] = mapped_column(
        ForeignKey("datasource.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(512))
    owner: Mapped[Optional[str]] = mapped_column(String(128))
    comment: Mapped[Optional[str]] = mapped_column(String(512))
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)  # 时间戳增量
