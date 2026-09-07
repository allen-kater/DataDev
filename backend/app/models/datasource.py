"""datasource：数据源。

铁律 1：host 一律存 IP，不存 hostname。
密码字段存 AES 加密密文（Phase 3 实现加密），本骨架只定义结构。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Datasource(Base):
    __tablename__ = "datasource"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # HIVE / MYSQL / POSTGRESQL
    host: Mapped[str] = mapped_column(String(128), nullable=False)
    hms_jdbc_url: Mapped[Optional[str]] = mapped_column(String(512))
    hms_user: Mapped[Optional[str]] = mapped_column(String(64))
    hms_password_enc: Mapped[Optional[str]] = mapped_column(String(512))
    hs2_host: Mapped[Optional[str]] = mapped_column(String(128))
    hs2_port: Mapped[Optional[int]] = mapped_column(Integer, default=10000)
    hs2_user: Mapped[Optional[str]] = mapped_column(String(64))
    hs2_password_enc: Mapped[Optional[str]] = mapped_column(String(512))
    jdbc_url: Mapped[Optional[str]] = mapped_column(String(512))
    jdbc_user: Mapped[Optional[str]] = mapped_column(String(64))
    jdbc_password_enc: Mapped[Optional[str]] = mapped_column(String(512))
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
