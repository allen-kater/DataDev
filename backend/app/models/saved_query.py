"""saved_query：收藏的 SQL 查询（可升级为任务）。"""

from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SavedQuery(Base, TimestampMixin):
    __tablename__ = "saved_query"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512))
    sql_text: Mapped[Optional[str]] = mapped_column(Text)
    datasource_id: Mapped[Optional[int]] = mapped_column(ForeignKey("datasource.id"))
